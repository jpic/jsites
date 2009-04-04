import jsites
from structure.items import *
import models
from django.contrib.auth.models import User
#from jsites.controllers.user import UserController, UserProfileController

staff = jsites.ControllerNode.factory('itbm',
    urlname='staff',
    name='Chocolat pistache: backoffice'
)
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
            ('creation_date', 'deadline', 'price', 'workflow_status',),
        )}),
    )
    #structure_class = TicketNode

staff.unregister_controller_for_content_class(models.Ticket)
staff.register(TicketController)

class UserController(jsites.ModelFormController):
    content_class = User
    field_names_for_merged_formsets = ('profile',)

staff.unregister_controller_for_content_class(User)
staff.register(UserController)

#from structure import html
#c=TicketController(action_name='forms')
#f=c.form_class
#h=html.HtmlRenderer(TicketNode())
#print h.render()
#print c.content_fields
