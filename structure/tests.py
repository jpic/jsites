from django.test import TestCase
from items import *

class NodeTest(TestCase):
    def setUp(self):
        self.root = Node('root',
            nodes=Node('first',
                nodes=(Node('firstfirst'), Node('secondfirst')))
        )
    def test_getting_field_names(self):
        names = self.root.get_matching_leaf_names(editable=True, persistent=True)
        self.assertEquals(2, len(names))
        self.assertTrue('subfirst' in names)
        self.assertTrue('subsecondleaf' in names)

    def test_bind_values(self):
        pass

class HtmlRendererTest(TestCase):
    def test_render_node(self):
        pass

    def test_render_node_form(self):
        pass

__test__ = {"doctest": """
Anot`her way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}
