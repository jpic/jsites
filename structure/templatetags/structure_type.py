from django import template
register = template.Library()
from structure.items import Node, Leaf

@register.filter
def is_node(value):
    return isinstance(value, Node)

@register.filter
def is_leaf(value):
    if isinstance(value, Leaf):
        return True
    return False
