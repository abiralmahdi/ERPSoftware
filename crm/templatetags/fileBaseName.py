import os
from django import template

register = template.Library()

@register.filter
def filename(file_field):
    """Return only the base filename from a FileField."""
    if not file_field:
        return ''
    return os.path.basename(file_field.name)