from django import template
register = template.Library()
from copy import deepcopy
from django.utils.safestring import mark_safe

@register.filter
def prop(value, arg):
    object = arg
    prop = value

    field = object._meta.get_field_by_name(prop)[0]
    value = getattr(object, prop)

    if hasattr(field, 'rst'):
        from docutils import core
        parts = core.publish_parts(source=unicode(value),
                                   writer_name='html4css1')
        return mark_safe(parts['fragment'])

    if field.__class__.__name__ == 'ManyRelatedManager':
        if not field.count():
            return '0'
        
        html = '<ul>'
        for value in field.all():
            html += '<li>%s</li>' % (value,)
        html += '</ul>'
        return mark_safe(html)

    return value
