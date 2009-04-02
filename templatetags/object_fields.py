from django import template
register = template.Library()
from copy import deepcopy
from django.utils.safestring import mark_safe

@register.filter
def class_prop(value, arg):
    object = arg.__class__
    prop = value
    return getattr(object, prop)

@register.filter
def keyvalue(value, arg):
    object = arg
    key = value
    return object[key]

@register.filter
def prop(value, arg):
    object = arg
    prop = value
    return getattr(object, prop)

@register.filter
def model_prop(value, arg):
    object = arg
    prop = value

    field = object._meta.get_field_by_name(prop)[0]
    value = getattr(object, prop)

    if hasattr(field, 'rst'):
        from docutils import core
        parts = core.publish_parts(source=unicode(value),
                                   writer_name='html4css1')
        return mark_safe(parts['fragment'])

    if field.__class__.__name__ == 'ManyRelatedManager' \
        or field.__class__.__name__ == 'RelatedObject':
        if not getattr(object, prop).count():
            return '0'
        
        html = '<ul>'
        for value in getattr(object, prop).all():
            html += '<li>%s</li>' % (value,)
        html += '</ul>'
        return mark_safe(html)

    return getattr(object, prop)

@register.filter
def verbose_name(value):
    return value._meta.verbose_name

@register.filter
def verbose_name_plural(value):
    return value._meta.verbose_name_plural
