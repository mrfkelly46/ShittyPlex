from django.shortcuts import render
from django.http import HttpResponse
from .models import Movie

# Create your views here.

def movie_list(request):
    ##### Request Headers #####
    #   s1 => sort 1 (title, year, runtime, ...)
    #   s1o => sort 1 order (ascending, descending)
    #   s2 => sort 2 (title, year, runtime, ...)
    #   s2o => sort 2 order (ascending, descending)
    #   filters => filters to search with (director='ron', ...)

    ##### Sorting #####
    DEFAULT_SORT_1_ORDER = 'D'
    DEFAULT_SORT_1 = 'movie_added'
    DEFAULT_SORT_2_ORDER = 'A'
    DEFAULT_SORT_2 = 'movie_title'

    # If sorting was set by user, grab sorting order as well.
    # Otherwise, fall back to default sorting and sorting order.
    sort_1 = request.GET.get('s1')
    if sort_1 is not None:
        sort_1_order = request.GET.get('s1o')
    else:
        sort_1 = DEFAULT_SORT_1
        sort_1_order = DEFAULT_SORT_1_ORDER

    sort_2 = request.GET.get('s2')
    if sort_2 is not None:
        sort_2_order = request.GET.get('s2o')
    else:
        sort_2 = DEFAULT_SORT_2
        sort_2_order = DEFAULT_SORT_2_ORDER

    # If sorting is random, then make sure not to attempt reverse order -- breaks
    if sort_1 == "?":
        sort_1_order = 'A'
    if sort_2 == "?":
        sort_2_order = 'A'

    ##### Filtering #####
    filters = request.GET.get('filters') 
    filters_dict = get_filters(filters)

    # If filters were submitted AND no sorting options were submitted,
    # then sort by title and year for more logical result sorting
    if filters_dict and not request.GET.get('s1') and not request.GET.get('s2'):
        sort_1 = 'movie_title'
        sort_1_order = 'A'
        sort_2 = 'movie_year'
        sort_2_order = 'A'

    # Convert sorting to a string used in order_by()
    sort_1_str = ('' if sort_1_order == 'A' else '-') + sort_1
    sort_2_str = ('' if sort_2_order == 'A' else '-') + sort_2

    # Filter and order movies
    movies = Movie.objects.filter(**filters_dict).order_by(sort_1_str, sort_2_str)

    num_results = len(movies)
    is_mobile = request.user_agent.is_mobile
    return render(request, 'MovieDB/movie_list.html', {'movies': movies, "numResults": num_results, "isMobile": is_mobile})

def random(request):
    ##### Filtering #####
    filters = request.GET.get('filters')
    filters_dict = get_filters(filters)

    # Filter and randomly order movies, take the first result
    movie = Movie.objects.filter(**filters_dict).order_by('?').first()
    movies = []
    movies.append(movie) 

    num_results = 1
    is_mobile = request.user_agent.is_mobile
    return render(request, 'MovieDB/movie_list.html', {'movies': movies, "numResults": num_results, "isMobile": is_mobile})

def get_filters(filters):
    filters_dict = {}

    if filters:
        filter_ = filters.split(", ")
        for f in filter_:
            # Filters inputed as '<field>:<term>, <field>:<term>' e.g. 'director:Ron Howard, rated:R'
            temp = f.split(":")
            # If no field declared, assume it is title
            if len(temp) == 1:
                filters_dict['movie_title__icontains'] = temp[0]
            else:
                filters_dict['movie_'+temp[0].lower()+'__icontains'] = temp[1]

    return filters_dict
