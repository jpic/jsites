from django.forms import widgets
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.conf import settings
from django.forms.util import flatatt

class WysiwygWidget(widgets.Textarea):
    class Media:
        js = ('jquery.wysiwyg.js',)
        css = {'all': ('jquery.wysiwyg.css',)}

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
            'jquery-ui.js',
            'jquery.asmselect.js',
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

class ForeignKeySearchInput(widgets.HiddenInput):
    class Media:
        js = (
            'jquery.bgiframe.min.js',
            'jquery.ajaxQueue.js',
            'jquery.autocomplete.min.js',
        )
        css = {
            'all': ('jquery.autocomplete.css',),
        }

    """
    A Widget for displaying ForeignKeys in an autocomplete search input 
    instead in a <select> box.
    """
    def label_for_value(self, value):
        return "label"
        key = self.rel.get_related_field().name
        obj = self.rel.to._default_manager.get(**{key: value})
        return truncate_words(obj, 14)

    def __init__(self, attrs=None, autocomplete_url='/autocomplete'):
        self.autocomplete_url = autocomplete_url
        super(ForeignKeySearchInput, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        rendered = super(ForeignKeySearchInput, self).render(name, value, attrs)
        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        html = rendered + u'''
            <style type="text/css" media="screen">
                #lookup_%(name)s {
                    padding-right:16px;
                    background: url(
                        %(admin_media_prefix)simg/admin/selector-search.gif
                    ) no-repeat right;
                }
                #del_%(name)s {
                    display: none;
                }
            </style>
<input type="text" id="lookup_%(name)s" value="%(label)s" />
<a href="#" id="del_%(name)s">
<img src="%(admin_media_prefix)simg/admin/icon_deletelink.gif" />
</a>
<script type="text/javascript">
            if ($('#lookup_%(name)s').val()) {
                $('#del_%(name)s').show()
            }
            $('#lookup_%(name)s').autocomplete('%(autocomplete_url)s').result(function(event, data, formatted) {
                if (data) {
                    $('#id_%(name)s').val(data[1]);
                    $('#del_%(name)s').show();
                }
            });
            $('#del_%(name)s').click(function(ele, event) {
                $('#id_%(name)s').val('');
                $('#del_%(name)s').hide();
                $('#lookup_%(name)s').val('');
            });
            </script>
        ''' % {
            'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
            'label': label,
            'name': name,
            'autocomplete_url': self.autocomplete_url,
        }
        return mark_safe(html)
