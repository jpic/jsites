import jsites
from structure.items import *
import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _

class ItbmSite(jsites.ControllerNode):
    media_overload = (
        '/home/jpic/sites/jtest/itbm/media',
        'media/',
    )

staff = ItbmSite.instanciate(
    urlname='staff',
    name='Chocolat pistache: backoffice'
)
staff.register_app('itbm')
staff.register_app('auth')

#class TicketNode(Node):
    #def __init__(self):
        #node = Node('title')
        #node.append(Leaf('title', editable=True, persistent=True))
        #node.append(Leaf('description', editable=True, persistent=True))
        #self.append(node)
        #node = Node('reason')
        #node.append(Leaf('price', editable=True, persistent=True))
        #node.append(Leaf('deadline', editable=True, persistent=True))
        #self.append(node)

class TicketController(jsites.ModelFormController):
    content_class = models.Ticket
    fieldsets = (
        ('Ticket', {'fields':(
            ('title', 'creator', 'owner',),
            ('description', 'components',),
            ('creation_date', 'deadline',),
            ('price', 'workflow_status',),
        )}),
    )
    constraints = (
        jsites.Constraint(('creator', 'owner'), 'title', 'foo'),
    )
    #structure_class = TicketNode

staff.unregister_controller_for_content_class(models.Ticket)
staff.register(TicketController)

class UserController(jsites.ModelFormController):
    content_class = User
    field_names_for_merge_formsets = ('profile',)
    fieldsets = (
        ('Utilisateur', {'fields': (
            ('username', 'password', 'current_ticket'),
            ('first_name', 'last_name', 'email'),
            ('is_staff', 'is_active', 'is_superuser'),
            ('last_login', 'date_joined'),
            ('groups', 'user_permissions'),
        )}),
    )

staff.unregister_controller_for_content_class(User)
staff.register(UserController)

#from structure import html
#c=TicketController(action_name='forms')
#f=c.form_class
#h=html.HtmlRenderer(TicketNode())
#print h.render()
#print c.content_fields
