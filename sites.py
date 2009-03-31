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
import widgets
from django.contrib.admin.util import flatten_fieldsets
from django.contrib.admin import helpers
from django.contrib.admin import widgets as admin_widgets
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

def media_converter(media, additionnal_js=(), additionnal_css={}):
    js = []
    for src in media.js + additionnal_js:
        if src[0] == '/':
            js.append(src)
        else:
            js.append('%sjs/%s' % (settings.JSITES_MEDIA_PREFIX, src))
    
    css={}
    for type in media.css:
        css[type] = []
        curcss = media.css[type]
        if type in additionnal_css:
            curcss+= additionnal_css[type]
        for src in curcss:
            if src[0] == '/':
                css[type].append(src)
            else:
                css[type].append('%scss/%s' % (settings.JSITES_MEDIA_PREFIX, src))
    
    return forms.Media(js=js, css=css)

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
            
            # its supposed to be a un-initialised variable
            # try to assign it from the class dict
            if name in self.__class__.__dict__:
                # TODO test the following
                # value = getattr(super(type, self.__class__), name)
                value = self.__class__.__dict__[name]
                setattr(self, name, value)
                return value

            # check if a missing getter caused the caugh AttributeError
            if name.find('get_') == 0:
                raise LazyGetterMissing(self, name)

            # call the getter and cache its return value in a property
            return self._set_and_get(name)
        return super(LazyProperties, self).__getattribute__(name)

    def _set_and_get(self, name):
        value = self._get(name)
        setattr(self, name, value)
        return value

    def _get(self, name):
        return getattr(self, self._getter(name))()

    def _getter(self, name):
        return 'get_' + name

    def _get_or_set(self, name, value):
        try:
            return getattr(self, name)
        except LazyGetterMissing:
            setattr(self, name, value)
        return getattr(self, name, value)

    def _hasanyof(self, names):
        for name in names:
            if self._has(name):
                return True
        return False

    def _hasvalue(self, name):
        return name in self.__class__.__dict__

    def _has(self, name):
        if name in self.__class__.__dict__ \
            or name in self.__dict__ \
            or hasattr(self, self._getter(name)):
            return True
        return False

class LazyGetterMissing(Exception):
    def __init__(self, raiser, name):
        msg = "Prop. %s missing from object %s of class %s (%s)" % (name, unicode(raiser), raiser.__class__.__name__, raiser.__class__ )
        super(LazyGetterMissing, self).__init__(msg)
# }}}
class UnnamedControllerException(Exception):
    def __init__(self, kwargs):
        msg = "Need either name or urlname or content_class in either: class attributes, Controller constructor arguments or Controller instance"
        super(UnnamedControllerException, self).__init__(msg)

class ControllerBase(LazyProperties):
    def __init__(self, inline=None, parent=None, **kwargs):
        """
        If a controller should pass itself to controllers it invokes as
        inlines using the "inline" argument.
    
        There should be no need for an inline controller to modify the
        properties of its caller.

        A ControllerNode instanciating a Controller should pass itself
        as 'parent'.
        """
        self.inline = inline
        self.parent = parent

        if self.inline:
            # reference to the "running" context
            self.request = self.inline.request
        
        self.kwargs = kwargs

        for property, value in kwargs.items():
            setattr(self, property, value)

        if not self._hasanyof(['content_class', 'name', 'urlname']):
            raise UnnamedControllerException(kwargs)

        if self._has('content_class'):
            self._get_or_set('name', self.content_class._meta.verbose_name)
            self._get_or_set('urlname', self.content_class._meta.module_name)
        elif self._has('name') and not self._has('urlname'):
            self.urlname = self.name
        elif self._has('urlname') and not self._has('name'):
            self.name = self.urlname

    # {{{ static/bootstrap: get_urls, instanciate, run.
    @classmethod
    def instanciate(self, **kwargs):
        return self(**kwargs)

    @classmethod
    def run(self, request, *args, **kwargs):
        self = self.instanciate(**kwargs)

        self.request = request
        self.args = args
        self.kwargs = kwargs
       
        # Run the action
        # It can override anything that was set by run()
        response = self.action()

        if response:
            return response

        return self.response

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
                        kwargs=dict(action_method_name=action_method_name, **self.kwargs),
                        )
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
    def get_media_path(self):
        return None
    def get_media(self):
        return media_converter(self._media, self.additionnal_js, self.additionnal_css)
    def get_additionnal_js(self):
        return ()
    def get_additionnal_css(self):
        return {}
    # }}}
    # {{{ context
    def get_context(self):
        context = {
            'controller': self,
            'media': self.media,
        }
        if self.parent:
            self.add_to_context('parent')
            context['menu'] = self.parent.menu
        return context

    def add_to_context(self, name):
        self.context[name] = getattr(self, name)
    # }}}
    # {{{ action, action_name
    def get_action_method_name(self):
        if 'action_method_name' in self.kwargs:
            return self.kwargs['action_method_name']
        else:
            return self.action_name

    def get_action_name(self):
        if 'action_name' in self.kwargs:
            return self.kwargs['action_name']
        else:
            return self.action_method_name

    def get_action(self):
        return getattr(self, self.action_name)
    # }}}
    # {{{ template, response
    def get_template(self):
        if not hasattr(self, 'action'):
            fallback = (
                'jsites/%s/index.html' % self.urlname,
                'jsites/index.html',
            )
        else:
            fallback = (
                'jsites/%s/%s.html' % (self.urlname, self.action.__name__),
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

class ModelController(ControllerBase):
# {{{ content_{class,id,fields,object}, fields_initial_values
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
# }}}
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

class ModelFormController(ModelController):
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
    def get_reuse_admin(self):
        return True

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
        
        self.media = self.media + self.form_object.media
        for formset_object in self.formset_objects:
            self.media += formset_object.media

        self.template = [
            'jsites/%s/forms.html' % self.urlname,
            'jsites/forms.html',
        ]

        if not self.reuse_admin:
            self.add_to_context('formset_objects')
            self.add_to_context('form_object')
        else:
            self.add_to_context('adminform_object')
            self.add_to_context('admin_formset_objects')
            core = settings.ADMIN_MEDIA_PREFIX+'js/core.js'
            i18n = settings.JSITES_MEDIA_PREFIX+'js/admin.jsi18n.js'
            self.media.add_js([core, i18n])

    def get_adminform_object(self):
        adminform_object = helpers.AdminForm(self.form_object, self.fieldsets, self.prepopulated_fields)
        return adminform_object

    def get_prepopulated_fields(self):
        return {}

    def get_flat_fieldsets(self):
        return flatten_fieldsets(self.fieldsets)

    def get_fieldsets(self):
        return [(None, {'fields': self.form_fields,})]

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

    def get_inline_fields(self):
        import copy
        fields = copy.copy(self.local_fields)
        fields.remove(self.inline_relation_field.name)
        return fields

    def get_flat_inline_fieldsets(self):
        return flatten_fieldsets(self.inline_fieldsets)

    def get_inline_fieldsets(self):
        return (None, {'fields': self.inline_fields})

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
        kwargs = {}
        if f.name in self.wysiwyg_field_names:
            kwargs['widget'] = widgets.WysiwygWidget
        elif isinstance(f, fields.DateField):
            kwargs['widget'] = admin_widgets.AdminDateWidget
        elif isinstance(f, fields.DateTimeField):
            kwargs['widget'] = admin_widgets.AdminDateTimeWidget
        elif isinstance(f, fields.TimeField):
            kwargs['widget'] = admin_widgets.AdminTimeWidget
        return f.formfield(**kwargs)

    def get_wysiwyg_field_names(self):
        return ('html','body')

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

    def formset_objects_factory(self, admin):
        """
        Return a list of formset objects.

        The form() view passes both the form_object and formset_objects.
        To set up the formset another controller would get in his list
        formset_objects, overload get_formset_object().

        Uses self.virtual_fields.
        """
        objects = []
        for prop in self.virtual_fields:
            object = self.formset_object_factory(prop, admin)
            objects.append(object)
        return objects

    def formset_object_factory(self, prop, admin):
        # figure what model we want an inline from
        related = self.content_class._meta.get_field_by_name(prop)[0].model
        # rely on the parent to get the controller class we want
        controller_class = self.parent.get_controller(related)
        # fire it as an inline of this controller
        controller = controller_class(self)
        # get the object we want
        if admin:
            object = controller.admin_formset_object
        else:
            object = controller.formset_object
        return object

    def get_admin_inline_options(self):
        class InlineAdminFormSetOptionsMock(object):
            def __init__(self, **kwargs):
                for property, value in kwargs.items():
                    setattr(self, property, value)
        options = InlineAdminFormSetOptionsMock(
            template=self.admin_inline_template,
            prepopulated_fields=self.prepopulated_fields,
            media=self.media,
            verbose_name_plural=self.content_class._meta.verbose_name_plural,
            verbose_name=self.content_class._meta.verbose_name
            #show_url=self.details_url,
        )
        return options

    def get_admin_inline_template(self):
        return 'admin/edit_inline/tabular.html'

    def get_admin_formset_object(self):
        object = helpers.InlineAdminFormSet(self.admin_inline_options, self.formset_object, self.fieldsets)
        return object

    def get_admin_formset_objects(self):
        return self.formset_objects_factory(True)

    def get_formset_objects(self):
        return self.formset_objects_factory(False)

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

    def get_inline_formset_fields(self):
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
    # }}}i

class ControllerNode(ControllerBase):
    actions = ('index',)
    def __init__(self, **kwargs):
        self._registry = {} # controller_class.content_class -> controller class
        super(ControllerNode, self).__init__(**kwargs)
    def get_menu(self):
        """
        Navigation is also the business of this router.
        """
        menu = menus.Menu()
        for controller in self._registry.values():
            menu += controller.get_menu()
        return menu
    # {{{ registry routines
    def register_named_crud(self, model_class, **kwargs):
        crud = ModelFormController
        object = crud(content_class=model_class, parent=self, **kwargs)
        self.register(object)

    def register(self, controller):
        for registered_controller in self._registry.values():
            if controller.urlname == registered_controller.urlname:
                raise AlreadyRegistered('A controller with urlname % is already registered in node %s' % (controller.name, self.name))

        controller.parent = self
        self._registry[controller.content_class] = controller

    def get_controller(self, model_class):
        return self._registry[model_class]
    # }}}
    def get_urls(self):
        urlpatterns = super(ControllerNode, self).get_urls()
        # Add in each model's views.
        for controller in self._registry.values():
            prefix = r'^%s/%s/' % (self.urlname, controller.urlname)
            route = url(prefix, include(controller.get_urls()))
            # TODO test the code commented below
            # route = url(prefix, include(controller_class))
            route = (prefix, include(controller.get_urls()))
            urlpatterns += patterns('', url(*route))
            if settings.DEBUG and controller.media_path:
                urlpatterns += self.get_static_url(controller.media_path)

        if settings.DEBUG:
            urlpatterns += self.get_static_url(jsites.__path__[0])
            print "%s urls fetched, visit /%s" % (self.name, self.urlname)
        return urlpatterns

    def get_static_url(self, path):
        path = '%s/media' % path
        urlpatterns = patterns('',
            (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
                {'document_root': path, 'show_indexes': True}),
        )
        return urlpatterns

    def index(self):
        if not settings.DEBUG:
            raise Exception('Cannot list controllers if not settings.DEBUG')
        self.context['controllers'] = self._registry.values()
    index = setopt(index, urlregex=r'^$', urlname='index')
