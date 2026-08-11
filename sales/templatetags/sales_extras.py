from django import template

register = template.Library()

@register.filter
def split(value, arg):
    if value is None:
        return []
    return str(value).split(arg)
