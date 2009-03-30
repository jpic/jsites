import re
from django import http, template
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render_to_response
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.template import RequestContext
from django.conf.urls.defaults import patterns, url, include
ERROR_MESSAGE = ugettext_lazy("Please enter a correct username and password. Note that both fields are case-sensitive.")
LOGIN_FORM_KEY = 'this_is_the_login_form'

from django import forms
from jadmin import menus
from django.forms.models import modelform_factory, inlineformset_factory, modelformset_factory

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

def setopt(func, *args, **kwargs):
    for arg in args:
        setattr(func, arg, True)
    for kwarg, value in kwargs.items():
        setattr(func, kwarg, value)
    return func

class LazyProperties(object):
    def __getattr__(self, name):
        try:
            return super(LazyProperties, self).__getattribute__(name)
        except AttributeError:
            # pass out if its not something we want to touch
            if name[:1] == '_':
                return super(LazyProperties, self).__getattribute__(name)
            # try to get it from class dict
            if name in self.__class__.__dict__:
                return self.__class__.__dict__[name]
            # try to find the getter
            getter = 'get_%s' % name
            setattr(self, name, getattr(self, getter)())
        return super(LazyProperties, self).__getattribute__(name)

    def reset(self, *variables):
        for name in variables:
            print 'resetting', name
            if name in self.__dict__:
                delattr(self, name)

class ControllerBase(LazyProperties):
    class Media:
        js = (
            'admin.urlify.js',
            'jquery.min.js',
            'jquerycssmenu.js',
        )
        css = {
            'all': ('jquerycssmenu.css', 'style.css'),
        }
    _media = Media

    def __init__(self, inline=None):
        self.inline = inline

    def get_media(self):
        js=['%s/js/%s' % (settings.JSITES_MEDIA_PREFIX, url) for url in self._media.js]
        css={}
        for type in self._media.css:
            css[type]=['%s/css/%s' % (settings.JSITES_MEDIA_PREFIX, url) for url in self._media.css[type]]
        return forms.Media(js=js, css=css)

    def prerun(self):
        """
        Default configuration assumes that:
        - each request can carry its own content_id and object
        This methods should be overloaded for controllers depending on one
        arbitary content_object and id: don't do the reset() call
        It should be overloaded and reset('content_class') should be called
        for controllers intended to use with different content_class, eliged
        per-request (in set_content_class()).

        Reseting 'response' is critical though, run() returns self.response
        to let the user create a self.reponse directly in the view, or
        call render_to_response otherwise.

        Anyway, if you're experiencing high WHF/minute at some point, then
        you probably forgot to reset a request-specific variable.
        """
        self.reset('content_id', 'content_object', 'fields_initial_values')
        self.reset('response', 'context', 'action', 'action_name')
        self.reset('template')
        self.reset('form_object', 'formset_object')
        # Todo: figure if that could be cached somehow (at least for parent menu)
        self.reset('menu')

    @classmethod
    def instanciate(self, inline=False):
        return self(inline)

    @classmethod
    def run(self, request, *args, **kwargs):
        self = self.instanciate()

        self.request = request
        self.args = args
        self.kwargs = kwargs
 
        # Allow cleaning variable cache
        self.prerun()
        
        # Run the action
        # It can override anything that was set by run()
        response = self.action()

        if response:
            return response

        return self.response

    @classmethod
    def get_urls(self): 
        urlpatterns = patterns('')
        for action_method_name in self.actions:
            action = getattr(self, action_method_name)
            if hasattr(action, 'decorate'):
                action = self.decorate_action(action)

            # name and regex are action function attributes
            if hasattr(action, 'urlname') and hasattr(action, 'urlregex'):
                urlname = action.urlname
                urlregex = action.urlregex
                urlpatterns += patterns('', 
                    url(urlregex,
                        self.run,
                        name=urlname,
                        kwargs={'action': action_method_name})
                )
        return urlpatterns

    def get_context(self):
        context = {
            'controller': self,
            'media': self.media,
        }
        if hasattr(self, 'parent'):
            context['parent'] = self.parent
            context['menu'] = self.parent.menu
        return context

    def add_to_context(self, name):
        self.context[name] = getattr(self, name)

    def get_content_id(self):
        if 'content_id' in self.kwargs:
            return self.kwargs['content_id']
        return None

    def get_content_object(self):
        if self.content_id:
            return self.content_class.objects.get(pk=self.content_id)
        # prepopulate where possible
        if self.fields_initial_values:
            return self.content_class(**self.fields_initial_values)
        return self.content_class()

    def get_fields_initial_values(self):
        from_get = {}
        for key, value in self.request.GET.items():
            if key in self.content_class._meta.get_all_field_names():
                from_get[key.encode()] = value
        return from_get

    def get_content_fields(self):
        return self.content_class._meta.get_all_field_names()

    def get_content_class(self):
        if self.content_object:
            return self.content_object.__class__

    def get_action_name(self):
        return self.kwargs['action']

    def get_action(self):
        return getattr(self, self.action_name)

    def get_template(self):
        if not hasattr(self, 'action'):
            fallback = (
                'jsites/%s/index.html' % self.name,
                'jsites/index.html',
            )
        else:
            fallback = (
                'jsites/%s/%s.html' % (self.name, self.action.__name__),
                'jsites/%s.html' % self.action.__name__,
            )
        return fallback

    def get_response(self):
        print "Response context", self.context
        return render_to_response(
            self.template,
            self.context,
            context_instance=RequestContext(self.request)
        )

class Controller(ControllerBase):
    actions = ('create', 'list', 'edit', 'details')

    @classmethod
    def get_menu(self):
        menu = menus.Menu()
        controller = menu.add(self.content_class._meta.verbose_name)
        controller.add('list', '/jtest/sitename/' + self.name)
        controller.add('create', '/jtest/sitename/' + self.name + '/create')
        return menu
    
    def details(self):
        self.add_to_context('content_object')
        self.add_to_context('content_fields')
    details = setopt(details, urlname='details', urlregex=r'^(?P<content_id>.+)/$')

    def formset(self):
        if self.request.method == 'POST':
            if self.formset_object.is_valid() and self.form_object.is_valid():
                self.save_form()
                self.save_formset()
        self.template = 'jsites/formset.html'
        self.add_to_context('formset_object')
        self.add_to_context('form_object')
    
    def edit(self):
        return self.formset()
    edit = setopt(edit, urlname='edit', urlregex=r'^edit/(?P<content_id>.+)/$')

    def create(self):
        return self.formset()
    create = setopt(create, urlname='create', urlregex=r'^create/$')

    def prerun(self):
        self.reset('form_object', 'search_engine')
        super(Controller, self).prerun()

    def save_form(self):
        self.model = self.form_object.save()

    def get_form_class(self):
        cls = self.content_class.__name__ + 'Form'
        return modelform_factory(
            fields=self.form_fields,
            model=self.content_class,
            formfield_callback=self.get_formfield
        )

    def get_form_fields(self):
        return None

    def get_formfield(self, f):
        return f.formfield()

    def get_form_object(self):
        if self.request.method == 'POST':
            form = self.form_class(self.request.POST, instance=self.content_object)
        else:
            form = self.form_class(instance=self.content_object)
        return form 

    def get_search_engine(self):
        import jsearch
        engine = jsearch.ModelSearch(
            model_class = self.content_class,
            queryset = self.queryset,
            search_fields = self.list_columns,
            form_class = self.form_class
        )
        return engine

    def get_list_columns(self):
        return self.form_fields

    def get_queryset(self):
        return self.content_class.objects.select_related()

    def list(self):
        self.search_engine.parse_request(self.request)
        self.add_to_context('search_engine')
        self.add_to_context('content_class')
        self.add_to_context('content_fields')
    list = setopt(list, urlname='list', urlregex=r'^$')

class ControllerWrapper(Controller): 
    actions = ('index',)

    def get_menu(self):
        menu = menus.Menu()
        for controller in self._registry.values():
            menu += controller.get_menu()
        return menu
 
    def __init__(self, *args, **kwargs):
        super(ControllerWrapper, self).__init__(*args, **kwargs)
        self._registry = {} # controller.name -> controller class
    
    def register(self, controller_class):
        if controller_class.name in self._registry.keys():
            raise AlreadyRegistered('A controller with name % is already registered on site %s' % (self.name, controller.name))

        controller_class.parent = self
        self._registry[controller_class.name] = controller_class

    def get_urls(self):
        urlpatterns = super(ControllerWrapper, self).get_urls()

        import jsites
        # Add in each model's views.
        print self._registry
        for controller_class in self._registry.values():
            print controller_class.name, controller_class.get_urls()
            urlpatterns += patterns('',
                url(r'^%s/%s/' % (self.urlname, controller_class.urlname), include(controller_class.get_urls())),
                (r'^media/(?P<path>.*)$', 'django.views.static.serve',
                    {'document_root': '%s/media' % jsites.__path__[0]}),
                )
        return urlpatterns

    def index(self):
        if not settings.DEBUG:
            raise Exception('Cannot list actions if not settings.DEBUG')
    index = setopt(index, urlregex=r'^$', urlname='index')
