class BaseTree(list):
    def render(self, ul=True):
        html = ''
        if ul:
            html += '<ul>'
        for treeitem in self:
            html += treeitem.render()
        if ul:
            html+= '</ul>'
        return html

    def add_link(self, title, url=None):
        if url and '/' not in url and len(url) > 0:
            url = reverse(url)
        item = LinkItem(title, url)
        self.append(item)
        return item

class LinkItem(BaseTree):
    def __init__(self, title, url = None):
        super(LinkItem, self).__init__()
        
        self.title = title
        if not url:
            self.url = ''
        else:
            self.url = url

    def render_inside(self):
        html = '<a href="' + self.url + '" title="' + self.title + '">' + self.title + '</a>'
        return html

    def render(self):
        inside = self.render_inside()
        if len(self) == 0:
            html = '<li>' + inside + '</li>'
        else:
            html = '<li>' + inside + '<ul>'
            for treeitem in self:
                html += treeitem.render()
            html+= '</ul></li>'
        return html

    def append_to_trees(self, trees):
        for tree in trees:
            tree.append(self)
        return self
