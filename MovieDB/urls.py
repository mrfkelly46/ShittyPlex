from django.urls import path

from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('random', views.random, name='random'),
]
