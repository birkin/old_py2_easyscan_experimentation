# -*- coding: utf-8 -*-

import os
from django.http import HttpResponse
from django.shortcuts import render


def js( request ):
    """ Returns javascript file.
        May switch to direct apache serving, but this allows the 'Request Scan' link to be set dynamically, useful for testing. """
    js_unicode = u''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    js_path = u'%s/lib/josiah_easyscan.js' % current_directory
    with open( js_path ) as f:
        js_utf8 = f.read()
        js_unicode = js_utf8.decode(u'utf-8')
    js_unicode = js_unicode.replace( u'HOST', request.get_host() )
    return HttpResponse( js_unicode, content_type = u'application/javascript; charset=utf-8' )


def home( request ):
    title = request.GET.get( 'title', u'' )
    callnumber = request.GET.get( 'call_number', u'' )
    barcode = request.GET.get( 'barcode', u'' )
    html = temp_html( title, callnumber, barcode )
    # return HttpResponse( html )
    data_dict = {}
    data_dict[u'foo'] = "bar"
    return render( request, u'easyscan_app_templates/base.html', data_dict )


def temp_html( title, callnumber, barcode ):
    html = u'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>easyscan data check</title>
    </head>
    <body>
        <p>Thanks for testing!</p>
        <p>The item info that would be processed...</p>
        <ul>
            <li>title: `%s`</li>
            <li>call-number, etc info: `%s`</li>
            <li>barcode: `%s`</li>
        </ul>
    </body>
    </html>''' % ( title, callnumber, barcode )
    return html
