# -*- coding: utf-8 -*-

import logging, os
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from easyscan_app import models


log = logging.getLogger(__name__)
request_validator = models.RequestValidator()
request_page_helper = models.RequestPageHelper()
barcode_validator = models.BarcodeValidator()


def js( request ):
    """ Returns javascript file.
        May switch to direct apache serving, but this allows the 'Request Scan' link to be set dynamically, useful for testing. """
    js_unicode = u''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    js_path = u'%s/lib/josiah_easyscan.js' % current_directory
    with open( js_path ) as f:
        js_utf8 = f.read()
        js_unicode = js_utf8.decode( u'utf-8' )
    js_unicode = js_unicode.replace( u'HOST', request.get_host() )
    return HttpResponse( js_unicode, content_type = u'application/javascript; charset=utf-8' )


def request_def( request ):
    """ Either displays login buttons, or a form to specify requested scan-content. """
    https_check = request_validator.check_https(
        request.is_secure(), request.get_host(), request.get_full_path() )
    if https_check[u'is_secure'] == False:
        return HttpResponseRedirect( https_check[u'redirect_url'] )
    if not u'authz_info' in request.session:
        request.session[u'authz_info'] = { u'authorized': False }
    data_dict = request_page_helper.build_data_dict( request )
    if request.session[u'authz_info'][u'authorized'] == False:
        return render( request, u'easyscan_app_templates/request_login.html', data_dict )
    else:
        return render( request, u'easyscan_app_templates/request_form.html', data_dict )


def shib_login( request ):
    log.debug( u'in shib_login()' )
    return HttpResponse( u'will handle shib-login' )


def barcode_login( request ):
    """ Displays barcode login form.
        Redirects to request form on success. """
    log.debug( u'in barcode_login()' )
    if request.method == u'POST':
        barcode_check = u'init'
        barcode_check = barcode_validator.check_barcode(
            request.POST.get(u'barcode', u''), request.POST.get(u'name', u'') )
        log.debug( u'in barcode_login(); barcode_check, `%s`' % barcode_check )
        if barcode_check[u'validity'] == u'valid':
            request.session[u'authz_info'][u'authorized'] = True
            request.session[u'user_info'] = { u'name': barcode_check[u'name'], u'email':barcode_check[u'email'] }
            redirect_url = u'https://%s%s' % ( request.get_host(), reverse(u'request_url') )
            return HttpResponseRedirect( redirect_url )
        return HttpResponse( u'submitted data will be handled here.' )
    else:
        data_dict = {
            u'title': request.GET.get( u'title', u'' ),
            u'callnumber': request.GET.get( u'callnumber', u'' ),
            u'barcode': request.GET.get( u'barcode', u'' ) }
        return render( request, u'easyscan_app_templates/barcode_login.html', data_dict )
