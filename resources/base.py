from django.conf.urls import defaults as urls
from django.core.urlresolvers import reverse
from django.conf import settings
from django import http
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404

from jpic import voodoo
from jpic import tree

from exceptions import *

class ResourceBase(voodoo.ppi):
    """
    The base resource is like a controller in <your favorite mvc framework>.

    It has his own set of actions, urls, and methods to generate a response.
    """

    def __init__(self, **kwargs):
        """
        Instanciate and validates the resource.

        :param inline: Resource that invokes this instance as an inline.
        :param parent: ResourceNode that manages routes to this resource.
        :param is_running: True when run() does self respawn.
        """
        if 'inline' not in kwargs:
            self.inline = None
        if 'parent' not in kwargs:
            self.parent = None
        if 'is_running' not in kwargs:
            self.is_running = False

        # call the parent to set each kwarg as a property
        super(ResourceBase, self).__init__(**kwargs)

        if self.inline:
            # reference to the "running" context
            self.request = self.inline.request

        # backup kwargs for get_url
        #TODO blacklist request specific stuff be default (not hardcode)
        self.kwargs = kwargs

        # validate resource
        if not self._hasanyof(['model_class', 'name', 'urlname']):
            raise UnnamedResourceException(kwargs)

        self.validate()

        # back up any variable to kwargs
        for kwarg in self.add_to_kwargs:
            self.kwargs[kwarg] = getattr(self, kwarg)

    def validate(self):
        if self._has('name') and not self._has('urlname'):
            self.urlname = self.name
        elif self._has('urlname') and not self._has('name'):
            self.name = self.urlname

    @classmethod
    def instanciate(self, **kwargs):
        """
        Return a new instance of the resource, with the givin kwargs 
        
        Used by run()
        """
        return self(**kwargs)

    @classmethod
    def run(self, request, *args, **kwargs):
        """
        This method should instanciate a resource, check if permissions
        are OK, run the action and return a response.

        If the action doesn't return a response (instance of
        django.http.HttpResponse), then self.get_response will be called
        through self.response.

        This allows to cache responses.
        """
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
        """
        Returns a url.patterns for all actions.

        This is configurable by setting options to an action method, ie:
        details = setopt(details, urlname='details', urlregex=r'^(?P<model_id>.+)/$')

        Other options are settable, but only urlname and urlregex are used here.
        """
        urlpatterns = urls.patterns('')
        for action_method_name in self.actions_names:
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

    def get_add_to_kwargs(self):
        """
        List of instance properties to copy to self.kwargs, done in __init__.

        For performance purposes, its possible to add values that are for example
        reversed from models definitions: get_formset_field_objects etc ...
        """
        return []

    def root_url(self):
        """
        Return the root url of the resource.

        It is not supposed to be hard coded.
        It prepends the urlname of the parent to its own urlname.
        """
        #TODO make recursive parent check
        if self.parent:
            return "/%s/%s" % (self.parent.urlname, self.urlname)
        else:
            return "/%s" % self.urlname

    def get_context(self):
        """
        Returns the context to use as base.
        
        By default, this adds the following variables:
        - resource is the instance,
        - media is self.media,
        - jsites_media_prefix is settings.JSITES_MEDIA_PREFIX
        - tree is self.tree or the paren't.
        - parent is the parent instance if any.
        """
        context = {
            'resource': self,
            'media': self.media,
            'jsites_media_prefix': settings.JSITES_MEDIA_PREFIX,
        }
        if self.parent:
            context['parent'] = self.parent
            context['tree'] = self.parent.tree
        else:
            context['tree'] = self.tree
        return context

    def add_to_context(self, name):
        """
        Copies a variable from this instance to self.context
        """
        self.context[name] = getattr(self, name)

    def get_permission(self, user=None, action_name=None, kwargs={}): # {{{ permissions
        """
        Wraps around check_permission, setting resource instance defaults
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
        Checks if a user can request an action with specified kwargs
        """ 
        return True
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
    
    def get_actions_names(self):
        return []
    # }}}
    # {{{ template, response
    def get_template(self):
        if not hasattr(self, 'action'):
            fallback = (
                '%s/index.html' % self.urlname,
                'index.html',
            )
        else:
            fallback = (
                '%s/%s.html' % (self.urlname, self.action.__name__),
                '%s.html' % self.action.__name__,
            )
        return fallback

    def get_response(self):
        return render_to_response(
            self.template,
            self.context,
            context_instance=RequestContext(self.request)
        )
    # }}}
    def get_media_path(self):
        return None
    def get_media(self):
        return voodoo.converter(js=self.js, css=self.css)
    def get_js(self):
        if self.parent:
            return self.parent.js
        return []
    def get_css(self):
        if self.parent:
            return self.parent.css
        return {
            'all': [],
            'screen': [],
            'projection': [],
        }
    def get_tree_items(self):
        """
        Optionnaly recursive dict of verbose_name -> url
        
        By default, it checks for the verbose_name option of all method names
        declared in this class actions, and uses get_action_url(action_method_name)
        to reverse the action url.
        """
        items = {}
        # try to add each action by default
        for action_method_name in self.actions_names:
            items[unicode(getattr(getattr(self, action_method_name), 'verbose_name'))] = self.get_action_url(action_method_name)
        return items

    def get_tree(self):
        """ Append all tree items to the parent tree, or a new tree instance """
        if self.parent:
            return self.parent.tree
        else:
            navtree = tree.BaseTree()

        return tree.LinkTreeFactory(self.tree_items, navtree).tree
