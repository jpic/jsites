from django import template
register = template.Library()
from django.utils.safestring import mark_safe

def resource_model_action_permission(resource, action, user, kwargs):
    return resource.get_permission(resource, action, user, kwargs)
