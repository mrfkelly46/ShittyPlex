from django.urls import path, re_path

from .views import general
from .views import auth

urlpatterns = [
    re_path('^$', general.movie_list, name='movie_list'),
    re_path('^random/$', general.random, name='random'),
]
