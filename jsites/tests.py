""" {{{
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
}}} """
from django.test import TestCase
from django.http import HttpRequest
import jsites
import sys
PROFILE=True

class ControllerTest(object):
    def setUp(self):
        self.c = None
        self.ci = None
        self.expected_variables = None
    def validate(self):
        if not self.expected_variables or not self.c or not self.ci:
            self.fail("I need to be setup, see CarControllerTest.setUp() for an example")

    def expected_properties_test(self, controller_object, expected_properties):
        for variable, value in expected_properties.items():
            self.expected_property_test(controller_object, variable, value)

    def expected_property_test(self, controller_object, variable, value):
        if PROFILE:
            print "Testing %s property %s" % (controller_object, variable)
        try:
            if issubclass(value, Exception):
                if PROFILE:
                    print ". Expecting an exception"
                try:
                    getattr(controller_object, variable)
                except value:
                    pass
        except TypeError:
            result = getattr(controller_object, variable)
            self.assertEquals(value, result,
                "Expected %s for %s, got %s instead" % (value,
                variable, result))

#class CarCreateTest(TestCase, ControllerTest):
    #def setUp(self):
        #self.c = site.get_controller(Car)
        #self.ci = self.c()
        #self.request = HttpRequest()
        #self.request.path = '/jtest/sitename/cars/create'
        #self.ci.request = self.request
        #self.ci.args = ()
        #self.ci.kwargs = {'action': 'create'}

    #def test_properties(self):
        #expected_properties = {
            #'content_fields': ['id', 'name', 'seats', 'weels'],
            #'local_fields': ['name'],
            #'formset_fields': ['name'],
            #'form_fields': ['name'],
            #'virtual_fields': ['seats', 'weels'],
            #'inline_formset_fields': jsites.NotAsInline,
            #'inline_relation_field': jsites.NotAsInline,
        #}
        #self.expected_properties_test(self.ci, expected_properties)
    
    #def test_inlines_properties(self):
        #c = site.get_controller(Seat)
        #ci = c(inline=self.ci)
        #expected_properties = {
            #'content_fields': ['car', 'foo', 'id'],
            #'local_fields': ['car', 'foo'],
            #'formset_fields': ['car', 'foo'],
            #'form_fields': ['car', 'foo'],
            #'virtual_fields': [],
            #'inline_formset_fields': ['foo'],
        #}
        #self.expected_properties_test(ci, expected_properties)
        #self.assertEqual('car',
            #ci.inline_relation_field.name,
            #"SeatController being instanciated as inline of CarController, 'car' was expected to be the inline_relation_field.name"
        #)
        #expected_properties = {
            #'virtual_fields': [],
            #'inline_formset_fields': ['foo'],
        #}
        #self.expected_properties_test(ci, expected_properties)

#class CarEditTest(CarCreateTest):
    #fixtures=['car1']
    #def setUp(self):
        #self.c = site.get_controller(Car)
        #self.ci = self.c()
        #self.request = HttpRequest()
        #self.request.path = '/jtest/sitename/cars/create'
        #self.ci.request = self.request
        #self.ci.args = ()
        #self.ci.kwargs = {'action': 'edit', 'content_id': 1}
        #self.expected_properties = {
        #'content_fields': ['id', 'name', 'seats', 'weels'],
        #'formset_fields': ['name'],
        #'form_fields': ['name'],
        #'virtual_fields': ['seats', 'weels'],
        #}

#""" {{{ SimpleTest
#class SimpleTest(TestCase):
    #def test_basic_addition(self):
        ## Tests that 1 + 1 always equals 2.
        #self.failUnlessEqual(1 + 1, 2)
#}}} """
#__test__ = {"doctest": """
#Testing content_class fields reflection

#"""}

