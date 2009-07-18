from django.test import TestCase

__test__ = {"doctest": """
>>> from jpic import tree
>>> t = tree.BaseTree()
>>> t.render(ul=False)
''
>>> t.render()
'<ul></ul>'
>>> t.append(tree.LinkItem('foo', '/bar'))
>>> t.render(ul=False)
'<li><a href="/bar" title="foo">foo</a></li>'
>>> t.render()
'<ul><li><a href="/bar" title="foo">foo</a></li></ul>'
>>> from copy import deepcopy
>>> tt = deepcopy(t)
>>> t.append(tt)
>>> t.render()
'<ul><li><a href="/bar" title="foo">foo</a></li><ul><li><a href="/bar" title="foo">foo</a></li></ul></ul>'
>>> t.render(ul=False)
'<li><a href="/bar" title="foo">foo</a></li><ul><li><a href="/bar" title="foo">foo</a></li></ul>'
>>> t = tree.BaseTree() 
>>> t.add_link('foo', '/bar')
[]
>>> t.render()
'<ul><li><a href="/bar" title="foo">foo</a></li></ul>'
>>> t.add_link('foo2', '/bar2').add_link('subfoo2', '/bar2/subfoo')
[]
>>> t.render()
'<ul><li><a href="/bar" title="foo">foo</a></li><li><a href="/bar2" title="foo2">foo2</a><ul><li><a href="/bar2/subfoo" title="subfoo2">subfoo2</a></li></ul></li></ul>'
>>> t1 = tree.BaseTree()
>>> t2 = tree.BaseTree()
>>> leaf = tree.LinkItem('foo', '/foo')
>>> leaf.append_to_trees((t1, t2))
[]
>>> t1.render()
'<ul><li><a href="/foo" title="foo">foo</a></li></ul>'
>>> t2.render()
'<ul><li><a href="/foo" title="foo">foo</a></li></ul>'
>>> from jpic import tree
>>> factory = tree.LinkTreeFactory({'root': {'foo': '/bar'}})
>>> factory.make()
[[[]]]
>>> factory.tree.render()
'<ul><li><a href="" title="root">root</a><ul><li><a href="/bar" title="foo">foo</a></li></ul></li></ul>'
>>> factory.tree.render(ul=False)
'<li><a href="" title="root">root</a><ul><li><a href="/bar" title="foo">foo</a></li></ul></li>'
"""}
