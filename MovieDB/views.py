from django.shortcuts import render
from django.http import HttpResponse
from .models import Movie

# Create your views here.

def movie_list(request):
    is_mobile = request.user_agent.is_mobile
    
    # First ordering option
    order1_asc = request.GET.get('order1Asc') or ''
    order1 = request.GET.get('order1') or 'movie_title'
    # if ordering is random, then make sure not to attempt reverse order -- breaks
    if order1 == "?":
        order1_asc = ''
    
    # Second ordering option
    order2_asc = request.GET.get('order2Asc') or ''
    order2 = request.GET.get('order2') or 'movie_year'
    # if ordering is random, then make sure not to attempt reverse order -- breaks
    if order2 == "?":
        order2_asc = ''

    # Filters
    filters_dict = {}

    filters = request.GET.get('filters')
    if filters:
        filter_ = filters.split(", ")
        for f in filter_:
            temp = f.split(":")
            # If no type declared, assume it is title
            if len(temp) == 1:
                filters_dict['movie_title__icontains'] = temp[0]
            else:
                filters_dict['movie_'+temp[0].lower()+'__icontains'] = temp[1]

    movies = Movie.objects.filter(**filters_dict).order_by(order1_asc+order1, order2_asc+order2)
    num_results = len(movies)
    return render(request, 'MovieDB/movie_list.html', {'movies': movies, "numResults": num_results, "isMobile": is_mobile})

 
