import os
import sys
import requests
from pprint import pprint

sys.path.append('/home/pi/django/ShittyPlex')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShittyPlex.settings')
import django
django.setup()

from MovieDB.models import Movie
from MovieDB.lib import MovieInfo, TMDB, parser

class MovieManager():
    def __init__(self, downloads='/home/pi/share/torrent-complete', storage='/home/pi/share/Movies'):
        self.downloads = downloads
        self.storage = storage
        self.api = MovieInfo()
        return

    def discover(self):
        paths = []
        for root, dirs, files in os.walk(self.downloads):
            for file in files:
                paths.append((root, file))

        movies = []
        for root, file in paths:
            info = parser.parse(file)
            if 'episode' in info:
                continue
            if 'extension' not in info:
                continue
            new_name = '({year}) {title}.{extension}'.format(**info)
            if info['extension'] == 'srt':
                new_name = '.'+new_name
            info['original_path'] = os.path.join(root, file)
            info['new_path'] = os.path.join(self.storage, new_name)
            movies.append(info)
        return movies

    def populate(self, movies):
        objs = []
        for movie in movies:
            og = {
                'title': movie['title'],
                'year': movie['year'],
                'extension': movie['extension'],
                'original_path': movie['original_path'],
                'new_path': movie['new_path'],
            }
            results = self.api.get(movie['title'], movie['year'])
            if results is None:
                print('API Error, adding empty entry...')
                obj, created = Movie.objects.update_or_create(title=og['title'], year=og['year'])
                obj.og = og
                objs.append(obj)
                continue
      
            pprint(results)
            poster_url = results.pop('poster')
            results['extension'] = og['extension']
            obj, created = Movie.objects.update_or_create(
                title=results['title'], year=results['year'],
                defaults={**results}
            )
            if created:
                print('Created!')
                print('getting movie poster...')
                poster = requests.get(poster_url)
                poster_path = '/home/pi/django/ShittyPlex/media/posters/{}.png'.format(obj.id)
                open(poster_path, 'wb').write(poster.content)
                obj.poster = 'posters/{}.png'.format(obj.id)
                obj.save()
            else:
                print('Updated!')
            obj.og = og
            objs.append(obj)
        return objs

    def create_links(self, movies):
        for movie in movies:
            src = movie.og['original_path']
            dst = movie.og['new_path']
            print('{} -?-> {}'.format(src, dst))
            if not os.path.exists(src):
                os.symlink(src, dst)
                print('Symlink made!')

def main():
    manager = MovieManager()
    movies = manager.discover()
    movies = manager.populate(movies)
    manager.create_links(movies)

if __name__ == '__main__':
    main()

