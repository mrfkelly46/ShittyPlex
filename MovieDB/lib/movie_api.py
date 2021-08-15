import os
import requests
import logging
from datetime import datetime
from pprint import pprint

print(os.environ.get('TMDB_KEY'))

logger = logging.getLogger(__name__)

class APIException(Exception):
    pass

class API():
    def __init__(self):
        return

    def query(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            logger.error('ERROR {}: {}'.format(response.status_code, url))
            raise APIException(response.status_code)
        return response.json()
     

class TMDB(API):
    API_KEY = os.environ.get('TMDB_KEY')
    BASE_URL = 'https://api.themoviedb.org/3/'
    SEARCH_URL = BASE_URL+'search/movie?api_key={api_key}&query={query}&year={year}'
    MOVIE_URL = BASE_URL+'movie/{movie_id}?api_key={api_key}&language=en-US'
    MOVIE_URL += '&append_to_reponse=external_ids,genres'
    IMAGES_URL = 'https://image.tmdb.org/t/p/w500'
    
    def __init__(self):
        super().__init__()

    def _get_best_result(self, title, year, results):
        if len(results) == 1:
            return results[0]
        matches = []
        most_popular = results[0]
        for result in results:
            if title == result['title'] and str(year) in result['release_date']:
                matches.append(result)
            if result['popularity'] > most_popular['popularity']:
                most_popular = result
        if matches == []:
            return most_popular
        most_popular = matches[0]
        for match in matches:
            if match['popularity'] > most_popular['popularity']:
                most_popular = match
        return most_popular
        
    def search(self, title, year, get=False):
        url = self.SEARCH_URL.format(api_key=self.API_KEY, query=title, year=year)
        response = self.query(url)
        result = None
        if response['total_results'] >= 1:
            result = self._get_best_result(title, year, response['results'])
        else:
            print('total_results == 0 for ({}) {}!'.format(year, title))
            logger.error('ERROR: No results for ({}) {}'.format(year, title))
            raise APIException('ERROR: No results')

        if get:
            tmdb_id = result['id']
            url = self.MOVIE_URL.format(movie_id=tmdb_id, api_key=self.API_KEY)
            movie = self.query(url)
            return movie
        
        return result

    def get(self, tmdb_id):
        url = self.MOVIE_URL.format(movie_id=tmdb_id, api_key=self.API_KEY)
        movie = self.query(url)
        return movie
        

class OMDB(API):
    API_KEY = os.environ.get('OMDB_KEY')
    MOVIE_URL = 'http://www.omdbapi.com/?apikey={api_key}&i={imdb_id}'
    
    def __init__(self):
        super().__init__()

    def search(self, title, year, get=False):
        raise NotImplementedError

    def get(self, imdb_id):
        url = self.MOVIE_URL.format(api_key=self.API_KEY, imdb_id=imdb_id)
        movie = self.query(url)
        return movie
        

class MovieAPI():
    def __init__(self):
        self.tmdb = TMDB()
        self.omdb = OMDB()

    def get(self, movie=None, title=None, year=None):
        info = {}

        if movie is not None:
            if movie.tmdb_id:
                info_tmdb = self.tmdb.get(movie.tmdb_id)
            else:
                try:
                    info_tmdb = self.tmdb.search(movie.title, movie.year, get=True)
                except APIException as e:
                    return None
        elif title is not None and year is not None:
            try:
                info_tmdb = self.tmdb.search(title, year, get=True)
            except APIException as e:
                return None
        else:
            raise Exception('Must provide either a MovieDB.Movie object, or a title and year')

        imdb_id = info_tmdb['imdb_id']
        release_date = datetime.strptime(info_tmdb['release_date'], '%Y-%m-%d')

        info_omdb = self.omdb.get(imdb_id)
        
        print('({}) {}'.format(release_date.year, info_tmdb['title']))
        info['tmdb_id']     = info_tmdb['id']
        info['title']       = info_tmdb['title']
        info['year']        = release_date.year
        if re.match('[?.!]$', info_omdb['Plot']):
            # Sometimes OMDB plots are truncated, if so instead use TMDB
            info['plot'] = info_omdb['Plot']
        else:
            info['plot'] = info_tmdb['overview']
        info['directors']   = info_omdb['Director']
        info['writers']     = info_omdb['Writer']
        info['actors']      = info_omdb['Actors']
        info['rated']       = info_omdb['Rated']
        info['released']    = release_date
        info['runtime']     = info_tmdb['runtime']
        info['genres']      = info_omdb['Genre']
        if info_tmdb['poster_path']:
            info['poster']      = self.tmdb.IMAGES_URL+info_tmdb['poster_path']
        else:
            info['poster'] = None
        info['imdb_rating'] = info_omdb['imdbRating']
        info['imdb_id']     = info_tmdb['imdb_id']
        return info
        
        
