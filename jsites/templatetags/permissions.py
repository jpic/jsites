from django import template
register = template.Library()
from django.utils.safestring import mark_safe

def controller_model_action_permission(controller, action, user, kwargs):
    return controller.get_permission(controller, action, user, kwargs)
