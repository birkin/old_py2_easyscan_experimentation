# -*- coding: utf-8 -*-

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render


def home( request ):
  return HttpResponse( u'<p>hello world</p>' )
