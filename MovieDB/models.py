from django.db import models

# Create your models here.

class Test(models.Model):
    test_header = models.CharField(max_length=200)
    test_date = models.DateTimeField('date published')

class Movie(models.Model):
    class Meta:
        unique_together = (('movie_title', 'movie_year'),)
    movie_title = models.CharField(max_length=100)
    movie_year = models.IntegerField()
    movie_added = models.TextField(null=True)
    movie_rated = models.TextField(null=True)
    movie_released = models.TextField(null=True)
    movie_runtime = models.IntegerField(null=True)
    movie_genre = models.TextField(null=True)
    movie_director = models.TextField(null=True)
    movie_writer = models.TextField(null=True)
    movie_actors = models.TextField(null=True)
    movie_plot = models.TextField(null=True)
    movie_poster = models.TextField(null=True)
    movie_imdbrating = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    movie_imdbvotes = models.IntegerField(null=True)
    movie_imdbid = models.TextField(null=True)
    manual = models.TextField(null=True)
    filepath = models.TextField(null=True)

