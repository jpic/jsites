import jsites
from structure.items import *
import models

staff = jsites.ControllerNode.factory('itbm',
    urlname='staff',
    name='Chocolat pistache: backoffice'
)
staff.unregister_controller_for_content_class(models.Ticket)

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

staff.register(TicketController)
print staff.get_controllers_for_content_class(models.Ticket)

#from structure import html
#c=TicketController(action_name='forms')
#f=c.form_class
#h=html.HtmlRenderer(TicketNode())
#print h.render()
#print c.content_fields
