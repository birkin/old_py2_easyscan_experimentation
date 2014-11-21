# -*- coding: utf-8 -*-

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render


def home( request ):
  title = request.GET.get( 'title', u'' )
  callnumber = request.GET.get( 'call_number', u'' )
  barcode = request.GET.get( 'barcode', u'' )
  resp = u'''
    <p>Thanks for testing!</p>
    <p>The item info that would be processed...</p>
    <ul>
      <li>Title: `%s`</li>
      <li>Callnumber, etc info: `%s`</li>
      <li>Barcode: `%s`</li>
    </ul>
    ''' % ( title, callnumber, barcode )

  return HttpResponse( resp )
