from django.contrib import admin
from .models import Fact
from .models import Movie
from .models import Profile

class FactAdmin(admin.ModelAdmin):
    list_display = ['text']

class MovieAdmin(admin.ModelAdmin):
    list_display = ['id', 'year', 'title', 'title_sort', 'title_search']
    list_editable = ['title_sort', 'title_search']
    search_fields = ['id', 'year', 'title', 'title_sort', 'title_search']
    list_filter = ['manual']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'tmdb_id' in form.changed_data:
            from MovieDB.lib import MediaManager
            manager = MediaManager()
            manager.update(obj)
        
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user']
    search_fields = ['user']
    filter_horizontal = ['watched', 'saved']

admin.site.register(Fact, FactAdmin)
admin.site.register(Movie, MovieAdmin)
admin.site.register(Profile, ProfileAdmin)

