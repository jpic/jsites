from django.utils.safestring import mark_safe

import items

class HtmlRenderer(object):
    def __init__(self, root, form_object=None):
        self.root = root
        self.form_object = form_object

    def render(self, node=None):
        if node == None:
            node = self.root

        html = u'<div class="grid_100">'
        for item in node:
            item_renderer = getattr(self, 'render_%s' % item.name, False)
            if item_renderer:
                html += item_renderer(item)
            elif isinstance(item, items.Node):
                html += self.render(item)
            else:
                html += u'<div class="grid_%s">' % (100/len(node))
                if item.editable and self.form_object:
                    html += '<label for="id_'+item.name+'">'
                    html += item.name
                    html += '</label>'
                    html += unicode(self.form_object[item.name])
                html += u'</div>'
        html += u'</div>'
        return mark_safe(html)
