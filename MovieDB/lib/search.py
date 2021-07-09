from MovieDB.lib import Query
from MovieDB.models import Movie

def search(q='', order_by_1='title_sort', order_by_2='year', user=None, watched=None, saved=None, streamable=None):
    movies = Movie.objects.prefetch_related('watched_by', 'saved_by').order_by(order_by_1, order_by_2)

    if q:
        query = Query(Movie, 'title_search')
        movies = query.get_query(q, movies)

    if user is not None and watched is not None:
        if watched == 'yes':
            movies = movies.filter(watched_by__user_id=user.profile)
        elif watched == 'no':
            movies = movies.exclude(watched_by__user_id=user.profile)

    if user is not None and saved is not None:
        if saved == 'yes':
            movies = movies.filter(saved_by__user_id=user.profile)
        elif saved == 'no':
            movies = movies.exclude(saved_by__user_id=user.profile)

    if streamable is not None:
        if streamable == 'yes':
            movies = movies.filter(extension__in=['mp4'])
        elif streamable == 'no':
            movies = movies.exclude(extension__in=['mp4'])

    if user is not None:
        movies = set_movie_info(movies, user)

    return movies

def set_movie_info(movies, user):
    if user is not None and user.is_authenticated:
        if isinstance(movies, Movie):
            movies = [movies]
        for movie in movies:
            movie.saved = user.profile in movie.saved_by.all()
            movie.watched = user.profile in movie.watched_by.all()
    return movies

