# vim: set fileencoding=utf8 :
# {{{ imports
import re
from django import http, template
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render_to_response
from django.utils.functional import update_wrapper
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.template import RequestContext
from django.conf.urls import defaults as urls
from django.core import urlresolvers
from django.core.urlresolvers import reverse
ERROR_MESSAGE = ugettext_lazy("Please enter a correct username and password. Note that both fields are case-sensitive.")
LOGIN_FORM_KEY = 'this_is_the_login_form'

from django import forms
from jadmin import menus
from django.forms.models import modelform_factory, inlineformset_factory, modelformset_factory
from django.db.models import fields
from django.db.models import related
from django.contrib.admin.util import flatten_fieldsets
import jsites
import widgets
from django.contrib.admin import helpers
from django.contrib.admin import widgets as admin_widgets
from ppv import jobject
from structure import items
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

# when this variable is enabled:
# things like loops that should happen in a template happen in python first
# this is only to make django useable with Werkzeug debugger
# set it to False if you ignore that Werkzeug debugger is insanely useful
TEST=False

class jSiteForm(helpers.AdminForm):
    def __init__(self, form, merged_formset_objects, *args):
        super(jSiteForm, self).__init__(form, *args)
        self.field_forms = {}
        for formset in merged_formset_objects.values():
            for field in formset.forms[0].fields:
                self.field_forms[field] = formset.forms[0]

    def __iter__(self):
        for name, options in self.fieldsets:
            yield jFieldset(self.form, self.field_forms, name, **options)

class jFieldset(helpers.Fieldset):
    def __init__(self, form, field_forms, name, **kwargs):
        super(jFieldset, self).__init__(form, name, **kwargs)
        self.field_forms = field_forms

    def __iter__(self):
        for field in self.fields:
            yield jFieldline(self.form, self.field_forms, field)

class jFieldline(helpers.Fieldline):
    def __init__(self, form, field_forms, field):
        super(jFieldline, self).__init__(form, field)
        self.field_forms = field_forms

    def __iter__(self):
        for i, field in enumerate(self.fields):
            yield jAdminField(self.form, self.field_forms, field, is_first=(i == 0))
    def errors(self):
        errors = []
        for field in self.fields:
            if field not in self.fields_forms:
                form = self.form
            else:
                form = self.field_forms[field]

            errors.append(form[field].errors.as_ul())

        return mark_safe(u'\n'.join(errors).strip('\n'))

class jAdminField(helpers.AdminField):
    def __init__(self, form, field_forms, field, is_first):
        if not field in field_forms:
            super(jAdminField, self).__init__(form, field, is_first)
        else:
            super(jAdminField, self).__init__(field_forms[field], field, is_first)

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

class UnnamedControllerException(Exception):
    def __init__(self, kwargs):
        msg = "Need either name or urlname or content_class in either: class attributes, Controller constructor arguments or Controller instance"
        super(UnnamedControllerException, self).__init__(msg)

class ControllerBase(jobject):
    def __init__(self, **kwargs):
        """
        If a controller should pass itself to controllers it invokes as
        inlines using the "inline" argument.
    
        There should be no need for an inline controller to modify the
        properties of its caller.

        A ControllerNode instanciating a Controller should pass itself
        as 'parent'.
        """
        if 'inline' not in kwargs:
            self.inline = None
        if 'parent' not in kwargs:
            self.parent = None
        if 'is_running' not in kwargs:
            self.is_running = False

        # ask parent to set each kwarg as a property
        super(ControllerBase, self).__init__(**kwargs)

        if self.inline:
            # reference to the "running" context
            self.request = self.inline.request

        # backup kwargs for get_url
        #TODO blacklist request specific stuff be default (not hardcode)
        self.kwargs = kwargs

        # validate controller
        if not self._hasanyof(['content_class', 'name', 'urlname']):
            raise UnnamedControllerException(kwargs)

        if self._has('content_class'):
            self._get_or_set('name', self.content_class._meta.verbose_name)
            self._get_or_set('urlname', self.content_class._meta.module_name)
        elif self._has('name') and not self._has('urlname'):
            self.urlname = self.name
        elif self._has('urlname') and not self._has('name'):
            self.name = self.urlname

        # back up any variable to kwargs
        for kwarg in self.backup_kwargs:
            self.kwargs[kwarg] = getattr(self, kwarg)
    
    def get_permission(self, user=None, action_name=None, kwargs={}):
        """
        Wraps around check_permission.
        """
        if not self.is_running and not user and not action_name:
            raise Exception("Not giving away a permission without action_name and user kwargs if not running")

        if not action_name:
            action_name = self.action_name
        if not user:
            user = self.request.user
        if not kwargs:
            kwargs = self.kwargs

        return self.check_permission(user, action_name, kwargs)

    def check_permission(self, user, action_name, kwargs):
        """
        This is what is supposed to be overloaded.
        """
        return True

# {{{ navigation/menu
    def get_menu_items(self):
        items = {}

        # try to add each action by default
        for action_method_name in self.actions:
            items[getattr(getattr(self, action_method_name), 'verbose_name').capitalize()] = self.get_action_url(action_method_name)

        return items

    def get_menu(self):
        if self.parent:
            return self.parent.menu

        menu = menus.Menu()
        # append a MenuItem for each menu_items to menus
        for name, url in self.menu_items.items():
            menu.add(name, url)
        return menu
# }}}
    # {{{ static/bootstrap: get_urls, instanciate, run.
    @classmethod
    def instanciate(self, **kwargs):
        return self(**kwargs)

    @classmethod
    def run(self, request, *args, **kwargs):
        self = self.instanciate(is_running=True, request=request, **kwargs)

        # do permission check after setup, but before
        # action call. This means you should not do
        # any critical model update/deletion before self.action()
        if not self.permission:
            return http.HttpResponseForbidden()

        # Run the action
        # It can override anything that was set by run()
        response = self.action()

        if isinstance(response, http.HttpResponse):
            return response

        return self.response

    def get_urls(self): 
        urlpatterns = urls.patterns('')
        for action_method_name in self.actions:
            action = getattr(self, action_method_name)
            if hasattr(action, 'decorate'):
                action = self.decorate_action(action)

            # name and regex are action function attributes
            if hasattr(action, 'urlname') and hasattr(action, 'urlregex'):
                urlname = action.urlname
                urlregex = action.urlregex
                name = ''
                if self.parent:
                    name += self.parent.urlname + '_'
                name += self.urlname + '_'
                name += urlname
                urlpatterns += urls.patterns('', 
                    urls.url(urlregex,
                        self.__class__.run,
                        name=name,
                        kwargs=dict(action_method_name=action_method_name, **self.kwargs),
                        )
                )
        return urlpatterns

    def get_backup_kwargs(self):
        return []

    def root_url(self):
        if self.parent:
            return "/%s/%s" % (self.parent.urlname, self.urlname)
        else:
            return "/%s" % self.urlname
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
            'jsites_media_prefix': settings.JSITES_MEDIA_PREFIX,
            'menu': self.menu,
        }
        if self.parent:
            context['parent'] = self.parent
            context['menu'] = self.parent.menu
        return context

    def add_to_context(self, name):
        self.context[name] = getattr(self, name)
    # }}}
    # {{{ action_url, action, action_name, action_method_name
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

    def get_action_url(self, action_name=None, kwargs=[]):
        if not action_name:
            if not self.is_running:
                raise Exception("Not giving an action url, for the current action if none is actually running")

            action_name = self.action_name

        if self.parent:
            prefix = "%s_%s_" % (self.parent.urlname, self.urlname)
        else:
            prefix = "%s_" % self.urlname

        self.kwargs.update(kwargs)
        return reverse(prefix+action_name, kwargs=kwargs)
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

    def get_content_field_names(self):
        return self.content_class._meta.get_all_field_names()

    def get_content_field_objects(self):
        objects = {}
        for name in self.content_field_names:
            objects[name] = self.content_class._meta.get_field_by_name(name)[0]
        return objects

    def get_content_object(self):
        if 'content_class' in self._security_stack:
            raise Exception('No way to figure content_object, content_class')

        if self.content_id:
            return self.content_class.objects.get(pk=self.content_id)

        # prepopulate where possible
        if self.fields_initial_values:
            return self.content_class(**self.fields_initial_values)
        return self.content_class()
    
    def set_content_object(self, content_object):
        self.content_object = content_object
        self.content_class = content_object.__class__
        self.content_id = content_object.pk

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
        for name, field in self.content_field_objects.items():
            if isinstance(field, related.RelatedObject) \
                and not isinstance(field, fields.AutoField):
                virtual_fields.append(field_name)
        return virtual_fields

    def get_inline_relation_field(self):
        if not self.inline:
            raise NotAsInline()

        for name, field in self.inline.content_field_objects.items():
            if not hasattr(field, 'field'):
                continue
            field = field.field
            if not hasattr(field, 'rel') or not hasattr(field.rel, 'to'):
                continue
            if field.rel.to == self.inline.content_class:
                return field
    # }}}
    def get_fk_fields(self):
        fields = []
        for field in self.content_class._meta.fields:
            if isinstance(field, related.ForeignKey):
                fields.append(field)
        return fields

    def details(self):
        self.add_to_context('content_object')
        self.add_to_context('content_field_names')
        self.add_to_context('content_field_objects')
    details = setopt(details, urlname='details', urlregex=r'^(?P<content_id>.+)/$', verbose_name='détails')

    def get_reverse_fk_field_names(self):
        names = []
        for name in self.content_class._meta.get_all_field_names():
            field = self.content_class._meta.get_field_by_name(name)[0]
            if isinstance(field, related.RelatedObject) and isinstance(field.field, related.ForeignKey):
                names.append(name)
        return names

    def get_reverse_fk_field_objects(self):
        return self.field_names_to_objects(self.reverse_fk_field_names)

    def field_names_to_objects(self, names):
        objects = {}
        for name in names:
            objects[name] = self.content_class._meta.get_field_by_name(name)[0]
        return objects

class ModelFormController(ModelController):
    actions = ('create', 'list', 'edit', 'details', 'delete')
    def delete(self):
        pass
    delete = setopt(delete, urlname='delete', urlregex=r'^delete/(?P<content_id>.+)/$', verbose_name=u'éffacer')

    def get_field_names_for_merged_formsets(self):
        """
        Return a list of field names which inline formsets should be part
        of the content object form.

        Its a template option.
        """
        return []

    # {{{ menu, get_action_url
    def get_menu_items(self):
        items = {}
        if self.is_running:
            if self.action_name == 'edit':
                items[self.edit.verbose_name] = self.get_action_url('details',  kwargs={'content_id': self.content_id})
            if self.action_name == 'details':
                items[self.edit.verbose_name] = self.get_action_url('edit',  kwargs={'content_id': self.content_id})
        
        items[self.list.verbose_name] = self.get_action_url('list')
        items[self.create.verbose_name] = self.get_action_url('create')

        return items
    # }}}
    # {{{ forms
    def get_use(self):
        return (
            'adminform_object',
            'adminformset_objects',
        )

    def forms(self):
        if self.request.method == 'POST':
            form_valid = False
            formsets_valid = False

            if self.form_object.is_valid():
                form_valid = True
                self.save_form()

                # set to true before elimination tests
                formsets_valid = True
                for formset in self.formset_objects.values():
                    if not formset.is_valid():
                        formsets_valid = False

            if form_valid and formsets_valid:
                self.save_formsets()
                return http.HttpResponseRedirect(self.get_action_url('details',kwargs={'content_id': self.content_id}))
            elif form_valid:
                return http.HttpResponseRedirect(self.get_action_url('edit',kwargs={'content_id': self.content_id}))

        # admin js deps (like jquery for jsites)
        if 'adminform_object' in self.use \
            or 'adminformset_objects' in self.use:
            core = settings.ADMIN_MEDIA_PREFIX+'js/core.js'
            i18n = settings.JSITES_MEDIA_PREFIX+'js/admin.jsi18n.js'
            self.media.add_js([core, i18n])

        # don't leave out any form/formset object media
        self.media += self.form_object.media
        for formset_object in self.formset_objects.values():
            self.media += formset_object.media

        # allow template overload per controller-urlname/action
        self.template = [
            'jsites/%s/forms.html' % self.urlname,
            'jsites/forms.html',
        ]

        # figure context
        if not 'adminform_object' in self.use:
            self.add_to_context('form_object')
        else:
            self.add_to_context('adminform_object')
        if not 'adminformset_objects' in self.use:
            self.add_to_context('formset_objects')
        else:
            self.add_to_context('admin_formset_objects')
        self.add_to_context('merged_formset_objects')

    def get_merged_formset_objects(self):
        """
        This is a formset registry like formset_objects, but it removes
        any formset_object that should be usable with the content_object
        jAdminForm, instead of having its own "tab".
        """
        merged_formset_objects = {} # new registry, like formset_objects

        for name in self.field_names_for_merged_formsets:
            # remove the formset from the regular registry and 
            # append it to this other registry
            merged_formset_objects[name] = self.formset_objects.pop(name)

            # also make sure there isn't any adminformset_object for it
            if 'adminformset_objects' in self.use:
                self.admin_formset_objects.pop(name)

        return merged_formset_objects

    def get_adminform_object(self):
        adminform_object = jSiteForm(self.form_object, \
            self.merged_formset_objects, self.fieldsets, \
            self.prepopulated_fields)
        return adminform_object

    def get_prepopulated_fields(self):
        return {}

    def get_flat_fieldsets(self):
        """Returns a list of field names from an admin fieldsets structure."""
        return flatten_fieldsets(self.fieldsets)

    def get_fieldsets(self):
        field_names = self.form_field_names

        # add field names of any formset to merge
        for formset in self.merged_formset_objects.values():
            field_names += formset.forms[0].fields.keys()

        return [(self.content_class._meta.verbose_name, {'fields': field_names,})]

    def edit(self):
        return self.forms()
    edit = setopt(edit, urlname='edit', urlregex=r'^edit/(?P<content_id>.+)/$', verbose_name=u'modifier')

    def create(self):
        return self.forms()
    create = setopt(create, urlname='create', urlregex=r'^create/$', verbose_name=u'créer (nouveau)')

    def save_form(self):
        #TODO implement __setattr__
        self.set_content_object(self.form_object.save())

    def get_form_class(self):
        """
        Returns a form class for self.content_class.

        Uses self.form_field_names, and self.formfield_for_dbfield
        as form field for db field callback.
        """
        cls = self.content_class.__name__ + 'Form'
        return modelform_factory(
            fields=self.form_field_names,
            model=self.content_class,
            formfield_callback=self.formfield_for_dbfield
        )

    def get_form_field_names(self):
        return self.local_field_names

    def get_form_field_objects(self):
        return self.field_names_to_objects(self.form_field_names)

    def get_inline_fields(self):
        import copy
        fields = copy.copy(self.local_fields)
        fields.remove(self.inline_relation_field.name)
        return fields

    def get_local_field_objects(self):
        objects = {}
        for name, field in self.content_field_objects.items():
            if not isinstance(field, (fields.AutoField, related.RelatedObject)):
                objects[name] = field
        return objects

    def get_local_field_names(self):
        return self.local_field_objects.keys()

    def formfield_for_dbfield(self, dbfield):
        """
        Default formfield for db field callback to use in our form generators.
        """
        kwargs = {}
        if dbfield.name in self.wysiwyg_fields:
            kwargs['widget'] = widgets.WysiwygWidget
        elif isinstance(dbfield, fields.DateField):
            kwargs['widget'] = admin_widgets.AdminDateWidget
        elif isinstance(dbfield, fields.DateTimeField):
            kwargs['widget'] = admin_widgets.AdminDateTimeWidget
        elif isinstance(dbfield, fields.TimeField):
            kwargs['widget'] = admin_widgets.AdminTimeWidget

        if self.action_name == 'list':
            kwargs['required'] = False

        formfield = dbfield.formfield(**kwargs)
        return formfield

    def get_wysiwyg_fields(self):
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
        for formset_object in self.formset_objects.values():
            formset_object.save()

    def formset_objects_factory(self, admin):
        """
        Return a list of formset objects.

        The form() view passes both the form_object and formset_objects.
        To set up the formset another controller would get in his list
        formset_objects, overload get_formset_object().

        Uses self.field_names_for_formsets.
        """
        objects = {}
        for name, field in self.field_objects_for_formsets.items():
            objects[name] = self.formset_object_factory(field, admin)
        return objects

    def formset_object_factory(self, prop, admin):
        # figure what model we want an inline from
        related = prop.model
        # rely on the parent to get the controller class we want
        controller_class = self.parent.get_controller_classes_for_content_class(related)
        # fire it as an inline of this controller, making sure we pass
        # the correct content_class: the related object we want
        kwargs = {
            'inline': self,
            'content_class': related,
            'inline_fk_name': prop.field.name
        }

        # make sure it won't give more than one formset_object in
        # this special case
        if prop.field.rel.related_name in self.field_names_for_formsets:
            kwargs['max_formsets_number'] = 1
            kwargs['formset_deletable'] = False

        controller_object = controller_class.instanciate(**kwargs)

        # get the object we want
        # run the getter: because this is a factory method,
        # and because else it won't know about the request!
        if admin:
            object = controller_object.get_admin_formset_object()
        else:
            object = controller_object.get_formset_object()
        return object

    def get_admin_inline_options(self):
        options = {}
        options["template"] = self.admin_inline_template
        options["prepopulated_fields"] = self.prepopulated_fields
        options["media"] = self.media
        options["verbose_name_plural"] = self.content_class._meta.verbose_name_plural
        options["verbose_name"] = self.content_class._meta.verbose_name
        # options["show_url"] = self.details_url,
        return options

    def get_admin_inline_options_mock(self):
        return self.admin_inline_options_mock_factory(**self.admin_inline_options)

    def admin_inline_options_mock_factory(self, **options):
        class InlineAdminFormSetOptionsMock(object):
            def __init__(self, **kwargs):
                for property, value in kwargs.items():
                    setattr(self, property, value)
        mock = InlineAdminFormSetOptionsMock(**options)
        return mock
    def get_admin_inline_template(self):
        return 'admin/edit_inline/tabular.html'

    def get_formset_fieldsets(self):
        return [(None, {'fields':self.inline_formset_field_names})]

    def get_admin_formset_object(self):
        object = helpers.InlineAdminFormSet(self.admin_inline_options_mock, self.formset_object, self.formset_fieldsets)
        if TEST:
            for inline_admin_form in object:
                for fieldset in inline_admin_form:
                    for line in fieldset:
                        if None in line:
                            print "GOTCHA"
                        for field in line:
                            if field is None:
                                print "NONE FIELD FOUND", object, inline_admin_form, fieldset ,line, field
        return object

    def get_admin_formset_objects(self):
        return self.formset_objects_factory(True)

    def get_formset_objects(self):
        if 'adminformset_objects' in self.use:
            formsets = {}
            for field_name, admin_formset_object in self.admin_formset_objects.items():
                formsets[field_name] = admin_formset_object.formset
            return formsets
        else:
            return self.formset_objects_factory(False)

    def get_formset_object(self, kwargs = {}):
        """
        Return a formset object.

        The formset object uses self.inline.content_object as related object
        instance if the controller was instanciated with the "inline" argument.

        Uses self.formset_fields or self.inline_formset_fields, if called by an
        a controller as inline.
        """
        if self.inline:
            kwargs['instance'] = self.inline.content_object
            # Also copy the request, as we want the other controller
            # to handle his formset
            self.request = self.inline.request
        else:
            kwargs['instance'] = self.content_object
        
        if self.request.method == 'POST':
            formset = self.formset_class(self.request.POST, **kwargs)
        else:
            formset = self.formset_class(**kwargs)

        return formset 

    def get_inline_fk_name(self):
        return None

    def get_extra_formsets(self):
        return 3

    def get_orderable_formsets(self):
        return False

    def get_max_formsets_number(self):
        return 20

    def get_formset_deletable(self):
        return self.get_permission(action_name='delete')

    def get_formset_class(self):
        """
        Returns a formset class.

        The formset class uses self.inline.content_class as related class
        if the controller was instanciated with the "inline" argument.

        Uses self.formset_fields, or self.inline_formset_fields.
        """
        kwargs = {}
        if self.inline:
            kwargs['fields'] = self.inline_formset_field_names
            kwargs['extra']  = self.extra_formsets
            kwargs['can_delete'] = self.formset_deletable
            kwargs['can_order']  = self.orderable_formsets
            kwargs['max_num'] = self.max_formsets_number
            
            if self.inline_fk_name: # use the fk_name if any
                kwargs['fk_name'] = self.inline_fk_name

            return inlineformset_factory(self.inline.content_class,
                self.content_class, **kwargs)
        else:
            kwargs['fields'] = self.formset_field_names
            return modelformset_factory(self.content_class, **kwargs)

    def get_field_names_for_formsets(self):
        return self.reverse_fk_field_names

    def get_field_objects_for_formsets(self):
        return self.field_names_to_objects(self.field_names_for_formsets)

    def get_formset_field_objects(self):
        return self.field_names_to_objects(self.formset_field_names)

    def get_formset_field_names(self):
        return self.local_field_names

    def get_inline_formset_field_objects(self):
        return self.field_names_to_objects(self.inline_formset_field_names)

    def get_inline_formset_field_names(self):
        return self.local_field_names
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
        return self.form_field_names

    def get_queryset(self):
        return self.content_class.objects.select_related()

    def list(self):
        self.search_engine.parse_request(self.request)
        self.add_to_context('search_engine')
        self.add_to_context('content_class')
        self.add_to_context('content_field_names')
        self.add_to_context('content_field_objects')
        # additionnal fancey links

    list = setopt(list, urlname='list', urlregex=r'^$', verbose_name=u'liste')
    # }}}

class StructureController(ModelFormController):
    def get_structure_object(self):
        return self.structure_class()
    def get_structure_class(self):
        return self.structure_object.__class__
    def get_html_structure_renderer_class(self):
        from structure import html
        return html.HtmlRenderer
    def get_html_structure_renderer_object(self):
        return self.html_structure_renderer_class(self.structure_object, self.form_object)
    def forms(self):
        super(StructureController, self).forms()
        self.add_to_context('structure_object')
        self.add_to_context('html_structure_renderer_object')
        self.template = [
            'jsites/%s/structured_forms.html' % self.urlname,
            'jsites/structured_forms.html',
        ]
    def get_content_field_names(self):
        return self.structure_object.get_matching_leaf_names(editable=True, persistent=True)

class ControllerNode(ControllerBase):
    actions = ('index',)
    instances = {}
    def __init__(self, **kwargs):
        # has a registry: is a singleton
        self.__class__.instance = self
        self._registry = {} # controller.name -> controller instance
        self._content_class_registry = {} # content_class -> controller instance
        super(ControllerNode, self).__init__(**kwargs)

    def get_menu(self):
        items = {self.name: {}}

        for controller in self._registry.values():
            items[unicode(self.name.capitalize())][unicode(controller.name.capitalize())] = controller.menu_items

        menu = menus.MenuFactories(items).menu

        return menu

    @classmethod
    def factory(self, app_name, **kwargs):
        if not 'urlname' in kwargs:
            kwargs['urlname'] = app_name
        node = self.instanciate(**kwargs)
        node.register_app(app_name)
        return node

    def register_app(self, app_name, **kwargs):
        """
        Ugly shortcut to get started visiting your app.
        """
        from django.db.models import get_app, get_models
        app = get_app(app_name)
        for content_class in get_models(app):
            self.register_named_crud(content_class)

    def register_named_crud(self, content_class, **kwargs):
        """
        Ugly shortcut to get started visiting your actions.
        """
        crud = ModelFormController
        object = crud(content_class=content_class, parent=self, **kwargs)
        self.register(object)

    def register(self, controller):
        """
        Registers a controller instance.

        Note that the controller will be re-instanciated in run(), by instanciate(),
        the only two class methods.
        get_urls() is charged of passing the arguments with which it was instanciated
        for later re-instanciation.
        """
        if isinstance(controller, type):
            if settings.DEBUG:
                print """Notice: register() converted controller class to instance
    Apparently, you're new to jsites. The differences between jsites and admin/databrowse registries are:
    - instances are registered, its the job of the controller instance get_urls() to pass static call to run() to urls.url(),
    - you can work with instances in your sites definition,
    - kwargs passed to the controller instance constructor are backed up in urls(),
    - add any "lazy" programmable property name to get_backup_kwargs() to add variables to backup (and not re-program at each run).
    You will notice that several controllers per model or several instances of the same controller class is planned to be supported,
    but it won't let you fine-tune formsets, because _content_class_registry only does register one controller per content_class, ATM.
"""
            controller = controller()

        for registered_controller in self._registry.values():
            if controller.urlname == registered_controller.urlname:
                raise AlreadyRegistered('A controller with urlname %s is already registered in node %s' % (controller.urlname, self.urlname))

        controller.parent = self
        self._registry[controller.urlname] = controller
        self._content_class_registry[controller.content_class] = controller

    def unregister_controller_for_content_class(self, content_class):
        controller = self._content_class_registry[content_class]
        del self._content_class_registry[content_class]
        del self._registry[controller.urlname]

    def get_controller_classes_for_content_class(self, content_class):
        """
        The trick allowing to use several controllers per model: use two registries.
        """
        if not content_class in self._content_class_registry:
            raise Exception('No controllers registered for content_class' % content_class)

        return self._content_class_registry[content_class].__class__

    def get_controllers_for_content_class(self, content_class):
        """
        The trick allowing to use several controllers per model: use two registries.
        """
        if not content_class in self._content_class_registry:
            raise Exception('No controllers registered for content_class' % content_class)

        return self._content_class_registry[content_class]

    def get_urls(self):
        """
        Takes care of prefixing inclusion of sub-controllers urls with controller.urlname.
        """
        urlpatterns = super(ControllerNode, self).get_urls()
        # Add in each model's views.
        for controller in self._registry.values():
            prefix = r'^%s/' % controller.urlname
            urlpatterns += urls.patterns('', urls.url(prefix, urls.include(controller.urls), kwargs={'parent': self}))
            if settings.DEBUG and controller.media_path:
                urlpatterns += self.get_static_url(controller.media_path)

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
        In debug mode, we want a list of controllers and actions that are registered.
        Should be improved: with links to actions.
        """
        if not settings.DEBUG:
            raise Exception('Cannot list controllers if not settings.DEBUG')
        
        self.context['nodes'] = {}

        for urlname, instance in self.__class__.instances.items():
            self.context['nodes'][urlname] = {}
            self.context['nodes'][urlname]['instance'] = instance
            self.context['nodes'][urlname]['controllers'] = instance._registry
        
        if TEST:
            for urlname, node in self.context['nodes'].items():
                print urlname, "CTRLS", node['controllers']
                for urlname, controller in node['controllers'].items():
                    print urlname, "CTRL", controller, controller.root_url()
    index = setopt(index, urlregex=r'^$', urlname='index', verbose_name=u'accueil')


"""
I know it wasn't the job of the controller to do all that. The only point of all this magic is to keep *just* sites configurationns all at one place,
In reality, i'm convinced that a well architectured framework should be built upon a tree configuration of sites with menus, actions configuration (url, callback, name, verbose name), models, and so on. That's for version 1, be in python, php whatever that's what i beleive a one-man-army it consultant needs.
"""
