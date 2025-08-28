from django import template

register = template.Library()

@register.filter
def to_str(value):
    """Convert value to string"""
    return str(value)