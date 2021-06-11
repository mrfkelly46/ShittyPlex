from django.urls import path

from . import views

app_name = 'MovieDB'

urlpatterns = [
    path('', views.home, name='home'),
    path('movie/<int:id>/', views.movie, name='movie'),
    path('movie/<int:id>/stream/', views.movie_stream, name='movie_stream'),
    path('movie/<int:id>/transcode/', views.movie_transcode, name='movie_transcode'),
    path('new/', views.new, name='new'),
    path('random/', views.random, name='random'),
    path('search/', views.search, name='search'),
    path('advanced_search/', views.advanced_search, name='advanced_search'),
    path('profile/', views.profile, name='profile'),
    path('get_new_movies/', views.get_new_movies, name='get_new_movies'),
]

