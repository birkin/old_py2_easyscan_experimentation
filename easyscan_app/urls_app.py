# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^request/$',  'easyscan_app.views.request_def', name=u'request_url' ),

    url( r'^josiah_easyscan.js/$',  'easyscan_app.views.js', name=u'js_url' ),  # this allows easy development, but in future, serve via apache directly

    url( r'^shib_login/$',  'easyscan_app.views.shib_login', name=u'shib_login_url' ),
    # url( r'^barcode_login/$',  'easyscan_app.views.barcode_login', name=u'barcode_login_url' ),  # 2012-Dec: no longer needed

    url( r'^confirmation/$',  'easyscan_app.views.confirmation', name=u'confirmation_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name=u'request_url') ),

    )
