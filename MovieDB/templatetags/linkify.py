import re

from urllib.parse import quote

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def linkify(string, field):
    links = []
    values = string.split(',')
    for value in values:
        _value = re.sub(r' ?\([^)]+\)', '', value).strip()
        query = '{0}="{1}"'.format(field, _value)
        links.append('<a class="quiet-link" href="/search?q={0}&list=1">{1}</a>'.format(quote(query), value))
    return mark_safe(', '.join(links))

