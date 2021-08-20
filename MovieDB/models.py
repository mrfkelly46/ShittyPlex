import os

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from datetime import datetime, timedelta


class Fact(models.Model):
    text = models.CharField(max_length=512)

    def __str__(self):
        return self.text

def subtitle_path(self, filename):
    return 'subtitles/{0}.vtt'.format(self.id)

class Movie(models.Model):
    title = models.CharField(max_length=128, db_index=True)
    year = models.IntegerField(db_index=True)
    title_sort = models.CharField(max_length=128)
    title_search = models.CharField(max_length=128)
    plot = models.TextField(max_length=512, blank=True, null=True)
    directors = models.TextField(blank=True, null=True)
    writers = models.TextField(blank=True, null=True)
    actors = models.TextField(blank=True, null=True)
    rated = models.CharField(max_length=16, blank=True, null=True)
    released = models.DateField(blank=True, null=True)
    runtime = models.IntegerField(blank=True, null=True)
    genres = models.TextField(blank=True, null=True)
    poster = models.ImageField(upload_to='posters', blank=True, null=True)
    subtitles = models.FileField(upload_to=subtitle_path, blank=True, null=True)
    imdb_rating = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    imdb_id = models.TextField(blank=True, null=True)
    tmdb_id = models.IntegerField(blank=True, null=True)
    added = models.DateField(default=datetime.now, blank=True, null=True, db_index=True)
    original_path = models.TextField(blank=True, null=True)
    path = models.TextField(blank=True, null=True)
    extension = models.CharField(max_length=8, blank=True, null=True)
    manual = models.BooleanField(default=False)

    @property
    def runtime_long(self):
        hours = self.runtime // 60
        minutes = self.runtime % 60
        string = ''
        if hours != 0:
            string += '{}h '.format(hours)
        if minutes != 0:
            string += '{}min'.format(minutes)
        return string.strip()

    @property
    def url(self):
        return '/video/{}'.format(os.path.basename(self.path))

    @property
    def sub_url(self):
        # TODO: Fix this bandaid
        try:
            # name = os.path.basename(self.path).split('.')[0] + '.srt'
            name = os.path.basename(self.path).split('.')[0] + '.vtt'
            return '/video/.{}'.format(name)
        except Exception as e:
            return e
        
    def update(self, **kwargs):
        if self._state.adding:
            raise self.DoesNotExist
        for field, value in kwargs.items():
            setattr(self, field, value)
        self.save(force_update=True)

    def __str__(self):
        return '({}) {}'.format(self.year, self.title)

    class Meta:
        unique_together = (('title', 'year'),)

@receiver(pre_save, sender=Movie)
def update_paths(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(id=instance.id)
    except sender.DoesNotExist:
        # Object is new/being created
        pass
    else:
        if obj.title != instance.title or obj.year != instance.year:
            # Title/year has changed, update file:
            new_path = os.path.dirname(os.path.abspath(instance.path))
            instance.title = instance.title.replace('/', '')
            new_path = os.path.join(new_path, '({movie.year}) {movie.title}.{movie.extension}'.format(movie=instance))
            os.rename(obj.path, new_path)
            # If original_path==path -> no symlink, set both to new path
            if instance.original_path == instance.path:
                instance.original_path = new_path
            instance.path = new_path

@receiver(post_delete, sender=Movie)
def remove_symlink(sender, instance, **kwargs):
    if instance.original_path != instance.path:
        if os.path.isfile(instance.path) and os.path.islink(instance.path):
            os.remove(instance.path)

##############################################################

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    watched = models.ManyToManyField(Movie, related_name='watched_by', blank=True)
    saved = models.ManyToManyField(Movie, related_name='saved_by', blank=True)

    def has_watched(self, movie):
        return self.watched.filter(id=movie.id).exists()

    def has_saved(self, movie):
        return self.saved.filter(id=movie.id).exists()

    def __str__(self):
        return str(self.user)

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

