from jpic.voodoo import setopt

from base import ResourceBase

class ResourceNode(ResourceBase):
    """
    The node resource is like a router, it wraps around a set of resources.

    It is also a singleton, because it holds a registry.
    """

    instances = {}

    def get_actions(self):
        return ('index',)
     
    def __init__(self, **kwargs):
        # has a registry: is a singleton
        self.__class__.instance = self
        self._registry = {} # resource.name -> resource instance
        super(ResourceNode, self).__init__(**kwargs)

    def get_menu(self):
        items = {self.name: {}}

        for resource in self._registry.values():
            items[unicode(self.name.capitalize())][unicode(resource.name.capitalize())] = resource.menu_items

        menu = menus.MenuFactories(items).menu

        return menu

    def register(self, resource):
        """
        Registers a resource instance.

        Note that the resource will be re-instanciated in run(), by instanciate(),
        the only two class methods.
        get_urls() is charged of passing the arguments with which it was instanciated
        for later re-instanciation.
        """
        if isinstance(resource, type):
            if settings.DEBUG and not self.__class__.warned:
                print """Notice: register() converted resource class to instance
    Apparently, you're new to jsites. The differences between jsites and admin/databrowse registries are:
    - instances are registered, its the job of the resource instance get_urls() to pass static call to run() to urls.url(),
    - you can work with instances in your sites definition,
    - kwargs passed to the resource instance constructor are backed up in urls(),
    - add any "lazy" programmable property name to get_add_to_kwargs() to add variables to backup (and not re-program at each run).
    You will notice that several resources per model or several instances of the same resource class is planned to be supported,
    but it won't let you fine-tune formsets, because _model_class_registry only does register one resource per model_class, ATM.
"""
            self.__class__.warned = True
            resource = resource()

        for registered_resource in self._registry.values():
            if resource.urlname == registered_resource.urlname:
                raise AlreadyRegistered('A resource with urlname %s is already registered in node %s' % (resource.urlname, self.urlname))

        resource.parent = self
        self._registry[resource.urlname] = resource

    def get_urls(self):
        """
        Takes care of prefixing inclusion of sub-resources urls with resource.urlname.
        """
        urlpatterns = super(ResourceNode, self).get_urls()
        # Add in each model's views.
        for resource in self._registry.values():
            prefix = r'^%s/' % resource.urlname
            urlpatterns += urls.patterns('', urls.url(prefix, urls.include(resource.urls), kwargs={'parent': self}))
            if settings.DEBUG and resource.media_path:
                urlpatterns += self.get_static_url(resource.media_path)

        if settings.DEBUG:
            urlpatterns += self.get_static_url(jsites.__path__[0])
            print "%s urls fetched, visit /%s" % (self.name, self.urlname)
        return urlpatterns

    def get_static_url(self, path):
        """
        Should be improved: allowing each application to have its own media repository.
        """
        path = '%s/media' % path
        urlpatterns = urls.patterns('',
            (r'^media/(?P<path>.*)$', 'django.views.static.serve',
                {'document_root': path, 'show_indexes': True}),
        )
        return urlpatterns

    @classmethod
    # singleton, for the registry
    def instanciate(self, **kwargs):
        if not 'urlname' in kwargs:
            raise Exception('Singletonning needs "urlname" in kwargs')

        if kwargs['urlname'] in self.instances:
            node = self.instances[kwargs['urlname']]
            for arg, value in kwargs.items():
                setattr(node, arg, value)
        else:
            node = self(**kwargs)
            self.instances[kwargs['urlname']] = node
        
        return self.instances[kwargs['urlname']]

    def index(self):
        """
        In debug mode, we want a list of resources and actions that are registered.
        Should be improved: with links to actions.
        """
        if not settings.DEBUG:
            raise Exception('Cannot list resources if not settings.DEBUG')
        
        self.context['nodes'] = {}

        for urlname, instance in self.__class__.instances.items():
            self.context['nodes'][urlname] = {}
            self.context['nodes'][urlname]['instance'] = instance
            self.context['nodes'][urlname]['resources'] = instance._registry
        
        if TEST:
            for urlname, node in self.context['nodes'].items():
                print urlname, "CTRLS", node['resources']
                for urlname, resource in node['resources'].items():
                    print urlname, "CTRL", resource, resource.root_url()
    index = setopt(index, urlregex=r'^$', urlname='index', verbose_name=u'accueil')


