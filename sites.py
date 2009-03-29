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

class ControllerBase(object): 
    def __init__(self, name):
        self.name = name
        self.urlname = name

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
                    url(
                        urlregex,
                        self.run,
                        name=urlname,
                        kwargs={'action': action_method_name})
                )
        
        return urlpatterns

    def get_context(self):
        context = {
            'controller': self,
        }
        if hasattr(self, 'parent'):
            context['parent'] = self.parent

        return context

    def reset(self, *variables):
        for variable in variables:
            if hasattr(self, variable):
                delattr(self, variable)

    def prerun(self):
        """
        Default configuration assumes that:
        - each request can carry its own content_id and object
        This methods should be overloaded for controllers depending on one
        arbitary content_object and id: don't do the reset() call
        It should be overloaded and reset('content_class') should be called
        for controllers intended to use with different content_class, eliged
        per-request (in set_content_class()).
        """
        self.reset('content_id', 'content_object')

    def run(self, request, *args, **kwargs):
        self.prerun()

        self.request = request
        self.args = args
        self.kwargs = kwargs
 
        # Set the global context
        self.context = self.get_context()
        # Set action method
        self.action = getattr(self, kwargs['action'])

        # Execute needed methods
        if hasattr(self.action, 'need'):
            for need in self.action.need:
                if not hasattr(self, need):
                    do = getattr(self, 'set_%s' % need)
                    do()
                self.context[need] = getattr(self, need)

        # Try to execute useful methods
        if hasattr(self.action, 'use'):
            for use in self.action.use:
                if not hasattr(self, use):
                    do = getattr(self, 'set_%s' % use, None)
                    try:
                        do()
                        self.context[need] = getattr(self, need)
                    except Exception:
                        pass
                else:
                    self.context[need] = getattr(self, need)
        
        # Run the action
        # It can override anything that was set by run()
        response = self.action()

        if response:
            return response

        print self.context

        # Wrap around 
        return self.get_response()

    def set_content_id(self):
        self.content_id = self.kwargs['content_id']
        print "Set content id"

    def set_content_object(self):
        if not hasattr(self, 'content_class'):
            self.set_content_class()
        if not hasattr(self, 'content_id'):
            self.set_content_id()
        self.content_object = self.content_class.objects.get(pk=self.content_id)

    def set_content_fields(self):
        if not hasattr(self, 'content_class'):
            self.set_content_class()
        self.content_fields = self.content_class._meta.get_all_field_names()

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
        if not hasattr(self, 'template'):
            self.template = self.get_template()
        if not hasattr(self, 'context'):
            self.context = self.get_context()

        return render_to_response(
            self.template,
            self.context,
            context_instance=RequestContext(self.request)
        )
 
    def urls(self):
        return self.get_urls()
    urls = property(urls)

class Controller(ControllerBase):
    actions = ('create', 'edit', 'details', 'list')
    
    def form(self):
        if self.request.method == 'POST' \
            and self.request.POST['submit'] == self.submit_name:

            if self.formobj.is_valid():
                self.save_form()
                if hasattr(self, 'save_revision'):
                    self.save_revision()
                self.inform_user_success()
                return self.redirect()
            else:
                self.inform_user_failure()
        
        return {'form': self.formobj}
    form = setopt(form, 'contribute_to_model', 'formobj')
    create = setopt(form, urlname='create', urlregex=r'^create/(.*)$')
    edit = setopt(form, urlname='edit', urlregex=r'^edit/(.*)$')

    def list(self):
        self.fields = self.get_fields()
        if not hasattr(self, 'get_list_qset'):
            raise Exception('get_list_qset not implemented in %s, cannot list.' % self.__class__.__name__)
        qs = self.get_list_qset()
        dict = {
            'object_list': self.get_list_qset(),
        }
        return dict
    list = setopt(list, urlname='list', urlregex=r'^$', need=('content_class'), use=('search_form'))

    def details(self):
        pass
    details = setopt(details, urlname='details', urlregex=r'^(?P<content_id>.+)/$', need=('content_object', 'content_fields'))

class ControllerWrapper(Controller): 
    actions = ('index',)

    def __init__(self, *args, **kwargs):
        super(ControllerWrapper, self).__init__(*args, **kwargs)
        self._registry = {} # controller.name -> controller class
    
    def register(self, controller):
        if controller.name in self._registry.keys():
            raise AlreadyRegistered('A controller with name % is already registered on site %s' % (self.name, controller.name))

        controller.parent = self
        self._registry[controller.name] = controller

    def get_urls(self):
        urlpatterns = super(ControllerWrapper, self).get_urls()

        # Add in each model's views.
        for controller in self._registry.values():
            urlpatterns += patterns('',
                url(r'^%s/%s/' % (self.urlname, controller.urlname), include(controller.urls))
                )
        return urlpatterns

    def index(self):
        if not settings.DEBUG:
            raise Exception('Cannot list actions if not settings.DEBUG')
    index = setopt(index, urlregex=r'^$', urlname='index')
