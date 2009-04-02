from django import template
register = template.Library()

@register.filter
def divideby(value, arg):
    return int(value) / int(arg)
