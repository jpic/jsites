from django.conf.urls.defaults import *

# ugly hack
urlpatterns = patterns('',)

from django.contrib import admin
# ugly hack that has bugs pending for months (can't re-register ...)
admin.autodiscover()
urlpatterns += patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
)

from django.contrib import databrowse
# ugly hack to force the user using a singleton
from itbm import databrowse
urlpatterns += patterns('',
    (r'^databrowse/(.*)', databrowse.site.root),
)

# getting started
import jsites
urlpatterns += patterns('',
    # usage:
    # (r'^app_label/', include(jsites.ControllerNode.factory('app_label').urls)),
    # example: 
    (r'^itbm/', include(jsites.ControllerNode.factory('itbm').urls)),
)

# single controller, multi-site example
from itbm.sites import site as itbm
urlpatterns += patterns('',
    # usage:
    # (r'^staff/',    include(staff.urls)),
    # (r'^partners/', include(partners.urls)),
    # example, main site controller:
    (r'^%s/' % itbm.urlname, include(itbm.urls)),
)
