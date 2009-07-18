# vim: set fileencoding=utf8 :
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
from ppi import jobject
from structure import items

# when this variable is enabled:
# things like loops that should happen in a template happen in python first
# this is only to make template crashes happen before django template
# takes the relay, making crashes debugable Werkzeug debugger
TEST=True

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

