# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^home/$',  'easyscan_app.views.home', name=u'home_url' ),

    url( r'^$', RedirectView.as_view(pattern_name='home_url') ),

    )
