# {{{ imports
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
from django.db.models import fields
from django.db.models import related
import jsites
# }}}
# {{{ Exceptions
class AlreadyRegistered(Exception):
    pass
class NotRegistered(Exception):
    pass
class NotAsInline(Exception):
    pass
# }}}
def setopt(func, *args, **kwargs): # {{{
    for arg in args:
        setattr(func, arg, True)
    for kwarg, value in kwargs.items():
        setattr(func, kwarg, value)
    return func
# }}}

class LazyProperties(object): # {{{
    PROFILE=False
    def __getattr__(self, name):
        try:
            return super(LazyProperties, self).__getattribute__(name)
        except AttributeError:
            if LazyProperties.PROFILE:
                print "AttributeError caugh in %s for %s" % (self.__class__, name)
            # pass out if its not something we want to touch
            if name[:1] == '_':
                return super(LazyProperties, self).__getattribute__(name)
            # don't let it recurse if something is not properly configured
            if name.find('get_get_') == 0:
                raise Exception("Recursion predicted in %s for attribute %s could not be found, please implement function %s" % (self.__class__, name, name[4:]))
            # try to get it from class dict
            if name in self.__class__.__dict__:
                return self.__class__.__dict__[name]
            # try to find the getter
            getter = 'get_%s' % name
            setattr(self, name, getattr(self, getter)())
        return super(LazyProperties, self).__getattribute__(name)
# }}}
class ControllerBase(LazyProperties):
    def __init__(self, inline=None):
        """
        If a controller should pass itself to controllers it invokes as
        inlines using the "inline" argument.
    
        There should be no need for an inline controller to modify the
        properties of its caller.
        """
        self.inline = inline

        if self.inline:
            # reference to the "running" context
            self.request = self.inline.request
            self.kwargs = self.inline.kwargs
            self.args = self.inline.args
    # {{{ static/bootstrap: get_urls, instanciate, run.
    @classmethod
    def instanciate(self, inline=False):
        return self(inline)

    @classmethod
    def run(self, request, *args, **kwargs):
        self = self.instanciate()
        self.request = request
        self.args = args
        self.kwargs = kwargs
       
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
    # }}}
    # {{{ media support
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
    def get_media(self):
        js=['%s/js/%s' % (settings.JSITES_MEDIA_PREFIX, url) for url in self._media.js]
        css={}
        for type in self._media.css:
            css[type]=['%s/css/%s' % (settings.JSITES_MEDIA_PREFIX, url) for url in self._media.css[type]]
        return forms.Media(js=js, css=css)
    # }}}
    # {{{ context
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
    # }}}
    # {{{ content_{class,id,fields,object}
    def get_content_class(self):
        if self.content_object:
            return self.content_object.__class__

    def get_content_id(self):
        if 'content_id' in self.kwargs:
            return self.kwargs['content_id']
        return None

    def get_content_fields(self):
        f = self.content_class._meta.get_all_field_names()
        return f

    def get_content_object(self):
        if self.content_id:
            return self.content_class.objects.get(pk=self.content_id)
        # prepopulate where possible
        if self.fields_initial_values:
            return self.content_class(**self.fields_initial_values)
        return self.content_class()
    # }}}
    # {{{ action, action_name
    def get_action_name(self):
        return self.kwargs['action']

    def get_action(self):
        return getattr(self, self.action_name)
    # }}}
    def get_fields_initial_values(self):
        """
        Parse the request and finds key/values matching self.content_class
        attribute.
        """
        from_get = {}
        for key, value in self.request.GET.items():
            if key in self.content_class._meta.get_all_field_names():
                from_get[key.encode()] = value
        return from_get
    # {{{ virtual_fields, inline_relation_fields (model re routines)
    def get_virtual_fields(self):
        """
        Returns a list of virtual field names, virtual fields are doable by
        setting 'related_name' in a FK pointing to self.content_class.
        """
        virtual_fields = []
        for field_name in self.content_fields:
            field = self.content_class._meta.get_field_by_name(field_name)[0]
            if isinstance(field, related.RelatedObject) \
                and not isinstance(field, fields.AutoField):
                virtual_fields.append(field_name)
        return virtual_fields

    def get_inline_relation_field(self):
        if not self.inline:
            raise NotAsInline()

        for field_name in self.inline.content_fields:
            field = self.inline.content_class._meta.get_field_by_name(field_name)[0]
            if not hasattr(field, 'field'):
                continue
            field = field.field
            if not hasattr(field, 'rel') or not hasattr(field.rel, 'to'):
                continue
            if field.rel.to == self.inline.content_class:
                return field
    # }}}
    # {{{ template, response
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
        return render_to_response(
            self.template,
            self.context,
            context_instance=RequestContext(self.request)
        )
    # }}}
class Controller(ControllerBase):
    actions = ('create', 'list', 'edit', 'details')    
    # {{{ menu
    @classmethod
    def get_menu(self):
        menu = menus.Menu()
        controller = menu.add(self.content_class._meta.verbose_name)
        controller.add('list', '/jtest/sitename/' + self.name)
        controller.add('create', '/jtest/sitename/' + self.name + '/create')
        return menu
    # }}}
    # {{{ details
    def details(self):
        self.add_to_context('content_object')
        self.add_to_context('content_fields')
    details = setopt(details, urlname='details', urlregex=r'^(?P<content_id>.+)/$')
    # }}}
    # {{{ forms
    def forms(self):
        if self.request.method == 'POST':
            valid = False
            if self.form_object.is_valid():
                valid = True
                for formset in self.formset_objects:
                    if not formset.is_valid():
                        valid = False
            if valid:
                self.save_form()
                self.save_formsets()
        self.template = 'jsites/formset.html'
        self.add_to_context('formset_objects')
        self.add_to_context('form_object')
    
    def edit(self):
        return self.forms()
    edit = setopt(edit, urlname='edit', urlregex=r'^edit/(?P<content_id>.+)/$')

    def create(self):
        return self.forms()
    create = setopt(create, urlname='create', urlregex=r'^create/$')

    def save_form(self):
        self.model = self.form_object.save()

    def get_form_class(self):
        """
        Returns a form class for self.content_class.

        Uses self.form_fields, and self.get_formfield
        as form field for db field callback.
        """
        cls = self.content_class.__name__ + 'Form'
        return modelform_factory(
            fields=self.form_fields,
            model=self.content_class,
            formfield_callback=self.get_formfield
        )

    def get_form_fields(self):
        return self.local_fields

    def get_inline_formset_fields(self):
        import copy
        fields = copy.copy(self.local_fields)
        fields.remove(self.inline_relation_field.name)
        return fields

    def get_local_fields(self):
        local_fields = []
        for field_name in self.content_fields:
            field = self.content_class._meta.get_field_by_name(field_name)[0]
            if not isinstance(field, (fields.AutoField, related.RelatedObject)):
                local_fields.append(field_name)
        return local_fields

    def get_formfield(self, f):
        """
        Default formfield for db field callback to use in our form generators.
        """
        return f.formfield()

    def get_form_object(self):
        """
        Returns a form object to edit self.content_object or create
        (instanciate and save) a self.content_class
        """
        if self.request.method == 'POST':
            form = self.form_class(self.request.POST, instance=self.content_object)
        else:
            form = self.form_class(instance=self.content_object)
        return form 

    def save_formsets(self):
        for formset_object in self.formset_objects:
            formset_object.save()

    def get_formset_objects(self):
        """
        Return a list of formset objects.

        The form() view passes both the form_object and formset_objects.
        To set up the formset another controller would get in his list
        formset_objects, overload get_formset_object().

        Uses self.virtual_fields.
        """
        objects = []
        for prop in self.virtual_fields:
            # figure what model we want an inline from
            related = self.content_class._meta.get_field_by_name(prop)[0].model
            # rely on the parent to get the controller class we want
            controller_class = self.parent.get_controller(related)
            # fire it as an inline of this controller
            controller = controller_class(self)
            # get its object_formset
            formset = controller.formset_object
            objects.append(formset)
        return objects

    def get_formset_object(self):
        """
        Return a formset object.

        The formset object uses self.inline.content_object as related object
        instance if the controller was instanciated with the "inline" argument.

        Uses self.formset_fields or self.inline_formset_fields
        """
        kwargs = {}
        if self.inline:
            kwargs['instance'] = self.inline.content_object
        else:
            kwargs['instance'] = self.content_object
        
        if self.request.method == 'POST':
            formset = self.formset_class(self.request.POST, **kwargs)
        else:
            formset = self.formset_class(**kwargs)
        return formset 

    def get_formset_class(self):
        """
        Returns a formset class.

        The formset class uses self.inline.content_class as related class
        if the controller was instanciated with the "inline" argument.

        Uses self.formset_fields, or self.inline_formset_fields.
        """
        kwargs = {}
        if self.inline:
            kwargs['fields'] = self.inline_formset_fields
            return inlineformset_factory(self.inline.content_class,
                self.content_class, **kwargs)
        else:
            kwargs['fields'] = self.formset_fields
            return modelformset_factory(self.content_class, **kwargs)

    def get_formset_fields(self):
        return self.local_fields

    # }}}
    # {{{ search/list view
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
    # }}}
class ControllerWrapper(Controller): 
    actions = ('index',)
    def __init__(self, *args, **kwargs):
        super(ControllerWrapper, self).__init__(*args, **kwargs)
        self._registry = {} # controller.name -> controller class
    # {{{ menu
    def get_menu(self):
        menu = menus.Menu()
        for controller in self._registry.values():
            menu += controller.get_menu()
        return menu
    # }}}
    # {{{ registry routines
    def register(self, model_class, controller_class):
        if controller_class.name in self._registry.keys():
            raise AlreadyRegistered('A controller with name % is already registered on site %s' % (self.name, controller.name))

        controller_class.parent = self
        controller_class.content_class = model_class
        self._registry[model_class] = controller_class

    def get_controller(self, model_class):
        return self._registry[model_class]
    # }}}
    def get_urls(self):
        urlpatterns = super(ControllerWrapper, self).get_urls()
        # Add in each model's views.
        for controller_class in self._registry.values():
            urlpatterns += patterns('',
                url(r'^%s/%s/' % (self.urlname, controller_class.urlname), include(controller_class.get_urls())),
                (r'^media/(?P<path>.*)$', 'django.views.static.serve',
                    {'document_root': '%s/media' % jsites.__path__[0]}),
                )
        return urlpatterns
    # {{{ site views
    def index(self):
        if not settings.DEBUG:
            raise Exception('Cannot list actions if not settings.DEBUG')
    index = setopt(index, urlregex=r'^$', urlname='index')
    # }}}
