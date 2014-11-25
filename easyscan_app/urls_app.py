# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^request/$',  'easyscan_app.views.request_def', name=u'request_url' ),

    url( r'^josiah_easyscan.js/$',  'easyscan_app.views.js', name=u'js_url' ),

    url( r'^login/$',  'easyscan_app.views.login', name=u'login_url' ),

    url( r'^$', RedirectView.as_view(pattern_name='request_url') ),

    )
