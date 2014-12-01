# -*- coding: utf-8 -*-

import logging, os
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render


log = logging.getLogger(__name__)


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
    https_check = helper_check_https(
        request.is_secure(), request.get_host(), request.get_full_path() )
    if https_check[u'is_secure'] == False:
        return HttpResponseRedirect( https_check[u'redirect_url'] )
    data_dict = {
        u'title': request.GET.get( u'title', u'' ),
        u'callnumber': request.GET.get( u'call_number', u'' ),
        u'barcode': request.GET.get( u'barcode', u'' )
        }
    return render( request, u'easyscan_app_templates/request.html', data_dict )


def helper_check_https( is_secure, get_host, full_path ):
    """ helper """
    if (is_secure == False) and (get_host != u'127.0.0.1'):
        redirect_url = redirect_url = u'https://%s%s' % ( get_host, full_path )
        log.debug( u'in views.helper_check_https(); redirect_url, `%s`' % redirect_url )
        return_dict = { u'is_secure': False, u'redirect_url': redirect_url }
    else:
        return_dict = { u'is_secure': True, u'redirect_url': u'N/A' }
    log.debug( u'in views.helper_check_https(); return_dict, `%s`' % return_dict )
    return return_dict


def shib_login( request ):
    log.debug( u'in views.shib_login' )
    return HttpResponse( u'will handle shib-login' )


def barcode_login( request ):
    log.debug( u'in views.barcode_login' )
    return HttpResponse( u'will handle barcode_login-login' )

