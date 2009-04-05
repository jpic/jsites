from django.forms import widgets
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.conf import settings

class WysiwygWidget(widgets.Textarea):
    class Media:
        js = (settings.JSITES_MEDIA_PREFIX+'js/jquery.wysiwyg.js',)
        css = {'all': (settings.JSITES_MEDIA_PREFIX+'/css/jquery.wysiwyg.css',)}

    def render(self, name, value, attrs={}):
        self.attrs['id'] = 'id_%s' % name
        html = super(WysiwygWidget, self).render(name, value, attrs)
        js = u"""
<script type="text/javascript">
    $("#%(id)s").wysiwyg();
</script>
        """ % self.attrs
        html+= js
        return mark_safe(html)

class AsmSelect(widgets.SelectMultiple):
    class Media:
        js = (
            settings.JSITES_MEDIA_PREFIX+'js/jquery-ui.js',
            settings.JSITES_MEDIA_PREFIX+'js/jquery.asmselect.js',
        )
        css = {
            'all': (settings.JSITES_MEDIA_PREFIX+'css/jquery.asmselect.css',)
        }
    def render(self, name, *args, **kwargs):
        html = u"""
    <script type="text/javascript">
        $(document).ready(function() {
            $("select[name=%s]").asmSelect({
                addItemTarget: 'bottom',
                sortable: true
            });   
        }); 
    </script>
        """ % name
        html += super(AsmSelect, self).render(name, *args, **kwargs)
        return mark_safe(html)
        
