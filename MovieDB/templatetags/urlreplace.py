from urllib.parse import urlencode
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    # Takes the current context's query args and adds the provided args from **kwargs
    # Used by our paginator to preserve any search parameters and add the page number
    query = context['request'].GET.copy()
    query.pop('page', None)
    query.update(kwargs)
    return query.urlencode()

