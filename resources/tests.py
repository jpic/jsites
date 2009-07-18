from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from jpic.resources import *
from jpic import voodoo

from django.conf.urls.defaults import *

class ResourceBaseExample(ResourceBase):
    actions_names = ('hello',)

    def hello(self):
        self.context['hello'] = 'Hello world'

    hello = setopt(
        hello,
        urlregex='^hello/$',
        urlname='hello',
        verbose_name=u'Hello'
    )

class ResourceBaseTest(TestCase):
    def test_validation(self):
        fail = True

        try:
            base = ResourceBaseExample()
        except UnnamedResourceException:
            fail = False

        self.assertFalse(fail, 
            'excepted ResourceBase to not let an un-named resource validate')

    def test_urls(self):
        base = ResourceBaseExample(name="example")
        self.assertEqual(len(base.urls), 1)
    
    def test_hello(self):
        base = ResourceBaseExample(name="example")
        response = base.hello()

    def test_run_hello(self):
        base = ResourceBaseExample(name="example")
        c = Client()

        response = c.get(reverse('example_hello'))
        
        self.assertEqual(response.template.name, 'example/hello.html')
        self.assertEqual(response.content, "Hello world\n")
