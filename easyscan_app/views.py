# -*- coding: utf-8 -*-

import logging, os
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from easyscan_app import models


log = logging.getLogger(__name__)
request_view_helper = models.RequestViewHelper()
barcode_view_helper = models.BarcodeViewHelper()


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
    https_check = request_view_helper.check_https(
        request.is_secure(), request.get_host(), request.get_full_path() )
    if https_check[u'is_secure'] == False:
        return HttpResponseRedirect( https_check[u'redirect_url'] )
    if not u'authz_info' in request.session:
        request.session[u'authz_info'] = { u'authorized': False }
    data_dict = request_view_helper.build_data_dict( request )
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
        return_response = barcode_view_helper.handle_post( request )
        return return_response
    else:
        data_dict = {
            u'title': request.GET.get( u'title', u'' ),
            u'callnumber': request.GET.get( u'callnumber', u'' ),
            u'barcode': request.GET.get( u'barcode', u'' ) }
        return render( request, u'easyscan_app_templates/barcode_login.html', data_dict )
