class BaseController(object):
    def __init__(self, name):
        self.name = name
        self.urlname = name

    def urlinfo(self):
        return (
            self.site.name,
            self.urlname,
        )
    urlinfo = property(urlinfo)
    
    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        info = self.admin_site.name, self.model._meta.app_label, self.model._meta.module_name

        urlpatterns = patterns('',
            url(r'^$',
                wrap(self.changelist_view),
                name='%sadmin_%s_%s_changelist' % info),
            url(r'^add/$',
                wrap(self.add_view),
                name='%sadmin_%s_%s_add' % info),
            url(r'^(.+)/history/$',
                wrap(self.history_view),
                name='%sadmin_%s_%s_history' % info),
            url(r'^(.+)/delete/$',
                wrap(self.delete_view),
                name='%sadmin_%s_%s_delete' % info),
            url(r'^(.+)/$',
                wrap(self.change_view),
                name='%sadmin_%s_%s_change' % info),
        )
        return urlpatterns

    def urls(self):
        return self.get_urls()
    urls = property(urls)
