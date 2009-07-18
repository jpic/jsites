from django import template
register = template.Library()
from copy import deepcopy
from django.utils.safestring import mark_safe
from django.db.models.fields import related

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
    return getattr(object, prop, None)

@register.filter
def model_prop(value, arg):
    object = arg
    prop = value

    field = object._meta.get_field_by_name(prop)[0]

    if hasattr(field, 'rst'):
        value = getattr(object, prop)
        from docutils import core
        parts = core.publish_parts(source=unicode(value),
                                   writer_name='html4css1')
        return mark_safe(parts['fragment'])

    # class defined in another class method: can't import it, zen.
    if field.__class__.__name__ == 'ManyRelatedManager' \
        or isinstance(field, related.RelatedObject) \
        or isinstance(field, related.ManyToManyField):

        try:
            count = getattr(object, prop).count()
        except Exception:
            prop = prop + '_set'
            count = getattr(object, prop).count()

        if not count:
            return '0'

        html = '<ul>'
        for value in getattr(object, prop).all():
            html += '<li>%s</li>' % (value,)
        html += '</ul>'

        return mark_safe(html)

    value = getattr(object, prop)
    return value

@register.filter
def verbose_name(value):
    return value._meta.verbose_name

@register.filter
def verbose_name_plural(value):
    return value._meta.verbose_name_plural
