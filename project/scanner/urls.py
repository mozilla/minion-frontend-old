# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.conf.urls.defaults import *

from . import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='scanner.home'),
    url(r'^new$', views.newscan, name='scanner.newscan'),
    url(r'^myscans$', views.myscans, name='scanner.myscans'),
    url(r'^scan/(?P<scan_id>[A-Za-z0-9\-]+)$', views.scan, name='scanner.scan'),
    url(r'^scan/(?P<scan_id>[A-Za-z0-9\-]+)/session/(?P<session_id>[A-Za-z0-9\-]+)/artifacts$', views.download_artifacts),
    url(r'^plans$', views.plans, name='scanner.plans'),
    url(r'^xhr_scan_status/?$', views.xhr_scan_status, name='scanner.xhr_scan_status'),
    url(r'^browserid/', include('django_browserid.urls')),
    url(r'^logout/?$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='scanner.logout'),
    url(r'^delete_scan$', views.delete_scan),
    url(r'^stop_scan$', views.stop_scan),
    url(r'^plan_details', views.plan_details),
)
