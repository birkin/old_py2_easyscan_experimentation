# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from easyscan_app import views


admin.autodiscover()


urlpatterns = [

    url( r'^request/$',  views.request_def, name='request_url' ),

    url( r'^info/$',  views.info, name='info_url' ),

    url( r'^shib_login/$',  views.shib_login, name='shib_login_url' ),
    url( r'^logout/$',  views.shib_logout, name='logout_url' ),

    url( r'^confirmation/$',  views.confirmation, name='confirmation_url' ),

    url( r'^stats_api/v1/$',  views.stats_v1, name='stats_v1_url' ),

    url( r'^admin/try_again/$',  views.try_again, name='try_again_url' ),
    url( r'^admin/try_again/confirm/(?P<scan_request_id>[^/]+)/$',  views.try_again_confirmation, name='try_again_confirmation_url' ),

    url( r'^dev_josiah_easyscan.js/$',  views.easyscan_js, name='easyscan_js_url' ),  # replaces hardcoded urls for easy local development
    url( r'^dev_josiah_request_item.js/$',  views.request_item_js, name='request_item_js_url' ),  # replaces hardcoded urls for easy local development

    url( r'^version/$',  views.version, name='version_url' ),

    url( r'^admin/', include(admin.site.urls)),

    url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

]
