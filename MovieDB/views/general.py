from django.shortcuts import render
from django.http import HttpResponse
from ..models import Movie

# Create your views here.

def movie_list(request):
    ##### Request Headers #####
    #   s1 => sort 1 (title, year, runtime, ...)
    #   s1o => sort 1 order (ascending, descending)
    #   s2 => sort 2 (title, year, runtime, ...)
    #   s2o => sort 2 order (ascending, descending)
    #   filters => filters to search with (director='ron', ...)
    context = {}

    ##### Sorting #####
    DEFAULT_SORT1_ORDER = 'des'
    DEFAULT_SORT1 = 'movie_added'
    DEFAULT_SORT2_ORDER = 'asc'
    DEFAULT_SORT2 = 'movie_title'

    # If sorting was set by user, grab sorting order as well.
    # Otherwise, fall back to default sorting and sorting order.
    sort1 = request.GET.get('sort1')
    if sort1 is not None:
        sort1_order = request.GET.get('sort1_order')
    else:
        sort1 = DEFAULT_SORT1
        sort1_order = DEFAULT_SORT1_ORDER

    sort2 = request.GET.get('sort2')
    if sort2 is not None:
        sort2_order = request.GET.get('sort2_order')
    else:
        sort2 = DEFAULT_SORT2
        sort2_order = DEFAULT_SORT2_ORDER

    # If sorting is random, then make sure not to attempt reverse order -- breaks
    if sort1 == "?":
        sort1_order = 'asc'
    if sort2 == "?":
        sort2_order = 'asc'

    ##### Filtering #####
    filters = request.GET.get('filters') 
    filters_dict = get_filters(filters)

    # If filters were submitted AND no sorting options were submitted,
    # then sort by title and year for more logical result sorting
    if filters_dict and not request.GET.get('sort1') and not request.GET.get('sort2'):
        sort1 = 'movie_title'
        sort1_order = 'asc'
        sort2 = 'movie_year'
        sort2_order = 'asc'

    context['filters'] = filters
    context['sort1'] = sort1
    context['sort1_order'] = sort1_order
    context['sort2'] = sort2
    context['sort2_order'] = sort2_order

    # Convert sorting to a string used in order_by()
    sort1_str = ('' if sort1_order == 'asc' else '-') + sort1
    sort2_str = ('' if sort2_order == 'asc' else '-') + sort2

    # Filter and order movies
    context['movies'] = Movie.objects.filter(**filters_dict).order_by(sort1_str, sort2_str)

    context['num_results'] = len(context['movies'])
    context['is_mobile'] = request.user_agent.is_mobile
    return render(request, 'MovieDB/movie_list.html', context)

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

