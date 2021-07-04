import os
import sys
import requests
import argparse
import subprocess
import logging
from pprint import pprint

sys.path.append('/home/pi/django/ShittyPlex')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShittyPlex.settings')
import django
django.setup()

from django.db.models import Q

from MovieDB.models import Movie
from MovieDB.lib import MovieAPI, parser, blacklist

logger = logging.getLogger(__name__)

class MediaManager():
    def __init__(self, interactive=False, discover_paths=None, storage='/home/pi/share/Movies'):
        self.interactive = interactive
        if discover_paths is None:
            self.discover_paths = [
                '/home/pi/share/torrent-complete',
                # '/home/pi/share/Movies',
            ]
        else:
            self.discover_paths = discover_paths
        self.storage = storage
        self.api = MovieAPI()
        return

    def get_runtime(self, filepath):
        try:
            runtime = subprocess.check_output(['ffprobe', '-i', filepath, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
            runtime = float(runtime) // 60
        except:
            runtime = 0
        return runtime

    def discover_files(self):
        paths = []
        for path in self.discover_paths:
            for root, dirs, files in os.walk(path):
                for file in files:
                    paths.append((root, file))

        movies = []
        television = []
        for root, file in paths:
            info = parser.parse(file)
            #print()
            print(root+'/'+file)
            pprint(info)
            if 'extras' in root.lower() and 'extras' not in file:
                #print('Skipping items in .../extras/...')
                continue
            if 'title' in info and info['title'].lower() in blacklist:
                #print('Skipping sample for "{}"'.format(file))
                continue
            if 'extension' not in info or info['extension']=='part':
                #print('Bad extension for "{}"'.format(file))
                continue
            if 'season' in info and 'episode' in info:
                #print('Skipping television "{}"'.format(file))
                continue
                new_name = 'S{season:02d}E{episode:02d} - {title}.{extension}'.format(**info)
                #TODO
            if 'title' not in info or info['title']=='':
                print(info)
                if self.interactive:
                    input('Could not find title for "{}/{}", skipping...'.format(root, file))
                else:
                    logger.warning('Could not find title for "{}/{}", skipping...'.format(root, file))
                continue
            if 'year' not in info:
                info['year'] = 9999
            new_name = '({year}) {title}.{extension}'.format(**info)
            info['original_path'] = os.path.join(root, file)
            info['new_path'] = os.path.join(self.storage, new_name)
            movies.append(info)

        return movies, television

    def get_new_movies(self):
        existing_movies = set()
        for movie in Movie.objects.all():
            existing_movies.add(movie.original_path)
            existing_movies.add(movie.path)
        
        count = 0

        movies, television = self.discover_files()
        for movie_info in movies:
            if movie_info['original_path'] in existing_movies or movie_info['new_path'] in existing_movies:
                continue
            runtime = self.get_runtime(movie_info['original_path'])
            if runtime < 40:
                continue
            info = {
                'title': movie_info['title'],
                'year': movie_info['year'],
                'original_path': movie_info['original_path'],
                'path': movie_info['new_path'],
                'extension': movie_info['extension'],
                'runtime': runtime,
                'title_sort': movie_info['title'],
                'title_search': movie_info['title'],
            }
            print()
            pprint(info)
            movie = Movie(**info)
            movie.save()
            print('Added "{movie.original_path}" to MovieDB as "({year}) {title}"'.format(movie=movie, year=info['year'], title=info['title']))
            if movie.original_path != movie.path and not os.path.exists(movie.path):
                os.symlink(movie.original_path, movie.path)
                print('    Symlink created: "{movie.path}"'.format(movie=movie))
            self.update(movie)
            count += 1
        print('Done!')
        return count

    def update(self, movie, get_poster=True):
        results = self.api.get(movie=movie)
        if results is None:
            if self.interactive:
                choice = input('API Error for "{movie}", search by title and year? [Y/N]: '.format(movie=movie))
                if choice.lower() == 'y':
                    title = input('  Title: ')
                    year = input('  Year: ')
                    results = self.api.get(title=title, year=year)
                    if results is None:
                        input('API Error for "({year}) {title}", skipping...'.format(year=year, title=title))
                        return
                else:
                    return
            else:
                logger.error('API Error for "{movie}"'.format(movie=movie))
                return
      
        print()
        pprint(results)

        # Set the runtime based on actual file when we first discover it
        results.pop('runtime')
        if results['imdb_rating'] == 'N/A':
            results['imdb_rating'] = 0

        poster_url = results.pop('poster')
        if not movie.poster or self.interactive or get_poster:
            get_poster = True
            if self.interactive:
                choice = input('Get movie poster for "({year}) {title}"? [Y/N] '.format(year=results['year'], title=results['title']))
                if choice.lower() != 'y':
                    get_poster = False
            if get_poster and poster_url:
                print('Getting movie poster for "{movie}"...'.format(movie=movie))
                poster = requests.get(poster_url)
                poster_path = '/home/pi/django/ShittyPlex/media/posters/{}.png'.format(movie.id)
                open(poster_path, 'wb').write(poster.content)
                movie.poster = 'posters/{}.png'.format(movie.id)
                movie.save()

        # Update title_search and title_sort
        results['title_search'] = results['title']
        results['title_sort'] = results['title']
        movie.update(**results)

    def update_all(self):
        movies = Movie.objects.filter(manual=False)
        for movie in movies:
            self.update(movie, get_poster=False)


def main():
    parser = argparse.ArgumentParser(description='Manage media for MovieDB')
    parser.add_argument('--get-new', action='store_true', default=False, dest='get_new')
    parser.add_argument('--update-all', action='store_true', default=False, dest='update_all')
    parser.add_argument('--prompts', action='store_true', dest='prompts')
    parser.add_argument('--no-prompts', action='store_false', dest='prompts')
    parser.set_defaults(prompts=True)

    args = parser.parse_args()
    
    manager = MediaManager(interactive=args.prompts)

    if args.get_new:
        manager.get_new_movies()

    if args.update_all:
        manager.update_all()

    if args.prompts:
        id = input('MovieDB ID: ')
        if not id:
            title = input('Title: ')
            year = input('Year: ')
        try:
            if id:
                movie = Movie.objects.get(id=id)
            else:
                movie = Movie.objects.get(title=title, year=year)
        except Movie.DoesNotExist:
            print('Movie not found')
        else:
            if movie.manual:
                input('Warning -- "{movie}" is set to manual. Do you want to overwrite? '.format(movie=movie))

            tmdb_id = input('Force TMDB id?: ')
            if tmdb_id:
                movie.tmdb_id = tmdb_id
                
            manager.update(movie)

    return

if __name__ == '__main__':
    main()

