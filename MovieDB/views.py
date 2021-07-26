import logging
import subprocess
from collections import OrderedDict

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.http import HttpResponse, StreamingHttpResponse
from django.views import View
from django.views.generic.detail import DetailView
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.template.loader import render_to_string

from MovieDB.models import Movie, Profile

from MovieDB.lib import search as db_search
from MovieDB.lib import set_movie_info
from MovieDB.lib import MediaManager
from MovieDB.lib import Query, Parser

logger = logging.getLogger(__name__)

def home(request):
    context = {}
    return render(request, 'MovieDB/home.html', context)

@csrf_exempt
def movie(request, id):
    context = {}
    movie = get_object_or_404(Movie, id=id)
    movie = set_movie_info([movie], user=request.user)[0]
    context['q'] = request.GET.get('q', None)

    # Handle updating the saved/watched status
    if request.POST and request.user.is_authenticated:
        profile = request.user.profile
        if request.POST.get('change') == 'watched':
            if movie.watched:
                profile.watched.remove(movie)
                return HttpResponse('REMOVED FROM WATCHED')
            else:
                profile.watched.add(movie)
                return HttpResponse('ADDED TO WATCHED')
        if request.POST.get('change') == 'saved':
            if movie.saved:
                profile.saved.remove(movie)
                return HttpResponse('REMOVED FROM SAVED')
            else:
                profile.saved.add(movie)
                return HttpResponse('ADDED TO SAVED')
        return HttpResponse('BAD')

    context['movie'] = movie
    return render(request, 'MovieDB/movie_detail.html', context)

def movie_stream(request, id):
    context = {}
    movie = get_object_or_404(Movie, id=id)
    if False:#movie.extension != 'mp4':
        messages.error(request, 'Cannot stream {} files, sorry...'.format(movie.extension))
        return redirect('MovieDB:movie', id=movie.id)
    movie = set_movie_info([movie], user=request.user)[0]
    context['movie'] = movie
    context['transcode'] = bool(request.GET.get('transcode'))
    if context['transcode']:
        messages.warning(request, 'Caution, you are using the experimental live transcoding option!')
    return render(request, 'MovieDB/stream.html', context)

def movie_transcode(request, id):
    movie = get_object_or_404(Movie, id=id)
    start = request.GET.get('start', 0)
    # If/when I add seeking, I think the "start" will actually be a Header set by the HTML5 video player.
    # Check out "Accept Ranges", "HTTP_RANGE", "Content-Range"
    # See: https://stackoverflow.com/questions/33208849/python-django-streaming-video-mp4-file-using-httpresponse
    def gen():
        cmd = [
            'ffmpeg',
            '-i', movie.path,
            '-ss', str(start),
            '-f', 'matroska',
            '-vcodec', 'h264',
            '-acodec', 'aac',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            # '-r', '15', # Frame rate
            # '-s', '800x600', # Size
            'pipe:1',
        ]
        tmp_log = open('/tmp/trans.log', 'w')
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=tmp_log)   
        logger.info('Transcoding!')
        try:
            size = 65536
            byte = proc.stdout.read(size)
            while byte:
                yield byte
                byte = proc.stdout.read(size)
        except Exception as e:
            logger.error(str(e))
        finally:
            proc.kill()
            tmp_log.close()
            logger.info('Transcoding stopped!')
    response = StreamingHttpResponse(gen(), content_type='video/webm')
    response['Access-Control-Allow-Origin'] = '*'
    response['Content-Disposition'] = 'inline'
    response['Content-Transfer-Encoding'] = 'binary'
    return response

def new(request):
    context = {}
    movies = db_search(order_by_1='-added', user=request.user)
    if len(movies) == 1:
        response = redirect('MovieDB:movie', id=movies[0].id)
        return response
    # context['movies'] = movies

    paginator = Paginator(movies, 20)
    page_number = request.GET.get('page')
    context['movies'] = paginator.get_page(page_number)

    return render(request, 'MovieDB/new.html', context)

def random(request):
    # Randomly order movies, take the first result
    context = {}
    movie = Movie.objects.all().order_by('?').first()
    if movie is not None:
        return redirect('MovieDB:movie', id=movie.id)
    messages.error(request, 'No movies found!')
    return redirect('MovieDB:home')
    
def search(request):
    context = {}
    q = request.GET.get('q')
    movies = db_search(q, user=request.user)
    if len(movies) == 1:
        response = redirect('MovieDB:movie', id=movies[0].id)
        response['Location'] += '?q=' + q
        return response
    context['q'] = q
    # context['movies'] = movies

    paginator = Paginator(movies, 20)
    page_number = request.GET.get('page')
    context['movies'] = paginator.get_page(page_number)

    query = Query(Movie, 'title_search', 'title')
    if q.strip():
        context['search_message'] = query.get_message(q)

    return render(request, 'MovieDB/search.html', context)

def advanced_search(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = None
    sort_options = OrderedDict()
    sort_options['Title (A to Z)'] = 'title_sort'
    sort_options['Title (Z to A)'] = '-title_sort'
    sort_options['Year (New to Old)'] = '-year'
    sort_options['Year (Old to New)'] = 'year'
    sort_options['Runtime (Short to Long)'] = 'runtime'
    sort_options['Runtime (Long to Short)'] = '-runtime'
    sort_options['IMDb Rating (High to Low)'] = '-imdb_rating'
    sort_options['IMDb Rating (Low to High)'] = 'imdb_rating'
    sort_options['Date Added (New to Old)'] = '-added'
    sort_options['Date Added (Old to New)'] = 'added'
    watched_options = OrderedDict()
    watched_options[''] = 'any'
    watched_options['Watched'] = 'yes'
    watched_options['Not Watched'] = 'no'
    saved_options = OrderedDict()
    saved_options[''] = 'any'
    saved_options['Saved'] = 'yes'
    saved_options['Not Saved'] = 'no'
    streamable_options = OrderedDict()
    streamable_options[''] = 'any'
    streamable_options['Streamable'] = 'yes'
    streamable_options['Not Streamable'] = 'no'
    context = {
        'sort_1': 'title',
        'sort_2': 'year',
        'watched': 'any',
        'saved': 'any',
        'streamable': 'any',
        'sort_options': sort_options,
        'watched_options': watched_options,
        'saved_options': saved_options,
        'streamable_options': streamable_options,
    }
    if request.GET:
        filters = request.GET.get('filters') 
        sort_1 = request.GET.get('sort_1')
        sort_2 = request.GET.get('sort_2')
        watched = request.GET.get('watched')
        saved = request.GET.get('saved')
        streamable = request.GET.get('streamable')
        if 'search' in request.GET:
            movies = db_search(filters, sort_1, sort_2, user, watched, saved, streamable)
            paginator = Paginator(movies, 20)
            page_number = request.GET.get('page')
            context['movies'] = paginator.get_page(page_number)
            # context['movies'] = movies
            context['num_results'] = len(context['movies'])
        elif 'random' in request.GET and request.is_ajax():
            movies = db_search(filters, '?', '?', user, watched, saved, streamable)
            context = {
                'movie': movies.first(),
                'detailed': True,
                'user': request.user,
            }
            html = render_to_string('MovieDB/movie.html', context)
            return HttpResponse(html)
        context['filters'] = filters
        context['sort_1'] = sort_1
        context['sort_2'] = sort_2
        context['watched'] = watched
        context['saved'] = saved
        context['streamable'] = streamable

    return render(request, 'MovieDB/advanced_search.html', context)

@login_required
def profile(request):
    context = {}
    return render(request, 'MovieDB/profile.html', context)

@login_required
def get_new_movies(request):
    if not request.user.is_staff:
        raise Http404
    manager = MediaManager()
    count = manager.get_new_movies()
    messages.success(request, 'Found <strong>{0}</strong> new movies'.format(count))
    return redirect('MovieDB:new')
    
