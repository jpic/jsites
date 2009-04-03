from jsites.tests import ControllerTest
from django.test import TestCase
from django.http import HttpRequest
import jsites
import sys
from models import *

site=jsites.ControllerNode.factory('itbm')

PROFILE=True
class TicketControllerTest(TestCase, ControllerTest):
    def setUp(self):
        global site
        self.ci = site.get_controllers_for_content_class(Ticket)
        self.c = self.ci.__class__
        self.request = HttpRequest()
        self.request.path = '/itbm/tickets/create'
        self.ci.request = self.request
        self.ci.args = ()
        self.ci.kwargs = {'action': 'create'}

    def test_properties(self):
        expected_properties = {
            'content_fields': [
                'components',
                'creation_date',
                'creator',
                'deadline',
                'description',
                'id',
                'owner',
                'price',
                'quotes',
                'title',
                'worked_on_by',
                'workflow_status',
            ],
            'local_fields': [
                'components',
                'creation_date',
                'creator',
                'deadline',
                'description',
                'owner',
                'price',
                'title',
                'workflow_status',
             ],
            'formset_fields': [
                'components',
                'creation_date',
                'creator',
                'deadline',
                'description',
                'owner',
                'price',
                'title',
                'workflow_status',
            ],
            'form_fields': [
                'components',
                'creation_date',
                'creator',
                'deadline',
                'description',
                'owner',
                'price',
                'title',
                'workflow_status',
            ],
            'virtual_fields': [
                'quotes',
                'worked_on_by',
            ],
            'reverse_fk_fields': [
                'worked_on_by',
            ],
            'inline_formset_fields': jsites.NotAsInline,
            'inline_relation_field': jsites.NotAsInline,
        }
        self.expected_properties_test(self.ci, expected_properties)
    
    def test_inlines_properties(self):
        global site
        ci = site.get_controllers_for_content_class(Quote)
        ci.inline = self.ci
        expected_properties = {
            'content_fields': [
                'creation_date',
                'id',
                'name',
                'tickets',
                'workflow_status',
            ],
            'local_fields': [
                'creation_date',
                'name',
                'tickets',
                'workflow_status',
            ],
            'formset_fields': [
                'creation_date',
                'name',
                'tickets',
                'workflow_status',
            ],
            'form_fields': [
                'creation_date',
                'name',
                'tickets',
                'workflow_status',
            ],
            'virtual_fields': [],
            'inline_formset_fields': [
                'creation_date',
                'name',
                'tickets',
                'workflow_status'
            ],
        }
        self.expected_properties_test(ci, expected_properties)
        self.assertEqual('tickets',
            ci.inline_relation_field.name,
            "QuoteController being instanciated as inline of TicketController, 'tickets' was expected to be the inline_relation_field.name"
        )
        expected_properties = {
            'virtual_fields': [],
            'inline_formset_fields': [
                'creation_date',
                'name',
                'tickets',
                'workflow_status',
            ],
        }
        self.expected_properties_test(ci, expected_properties)
