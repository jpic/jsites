import base

class LinkTreeFactory(object):
    def __init__(self, source, tree=None):
        self.source = source
        if not tree:
            tree = base.BaseTree()
        self.tree = tree

    def make(self):
        if isinstance(self.source, dict):
            self.parse_link_dict(self.source, self.tree)
        return self.tree

    def parse_link_dict(self, source, tree):
        if not isinstance(source, dict):
            raise Exception('%s is not a dict' % source)
        if not isinstance(tree, base.BaseTree):
            raise Exception('%s is not a tree' % tree)

        for k, v in source.items():
            if isinstance(v, dict):
                self.parse_link_dict(v, tree.add_link(k))
            else:
                tree.add_link(k, v)

        return tree
