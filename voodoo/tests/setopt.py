from django.test import TestCase

from jpic import voodoo

class SetoptTest(TestCase):
    def test_setopt(self):
        self.assertEqual(self.test_setopt.foo, 'bar')
    test_setopt = voodoo.setopt(test_setopt, foo='bar')
