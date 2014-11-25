# -*- coding: utf-8 -*-

import logging, os
from django.http import HttpResponse
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
    data_dict = {
        'title': request.GET.get( 'title', u'' ),
        'callnumber': request.GET.get( 'call_number', u'' ),
        'barcode': request.GET.get( 'barcode', u'' )
        }
    return render( request, u'easyscan_app_templates/request.html', data_dict )


def login( request ):
    log.debug( u'in login(); login_type, `%s`' % request.GET.get(u'login_type', u'') )
    log.debug( u'in login(); request.is_secure(), `%s`' % request.is_secure() )
    log.debug( u'in login(); request.get_host(), `%s`' % request.get_host() )
    if request.GET.get(u'login_type', u'') == u'Standard Shib Login':
        redirect_url = u''  # shib_login_url
    return HttpResponse( u'<p>patience, padawan, you must have</p>' )



# from django.core.urlresolvers import reverse
# entry[u'url'] = u'%s://%s%s' % ( url_scheme, server_name, reverse(u'inscription_url', args=(entry[u'id'],)) )
# request.is_secure(), request.get_host()
