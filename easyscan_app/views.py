# -*- coding: utf-8 -*-

from django.http import HttpResponse


def home( request ):
  title = request.GET.get( 'title', u'' )
  callnumber = request.GET.get( 'call_number', u'' )
  barcode = request.GET.get( 'barcode', u'' )
  html = temp_html( title, callnumber, barcode )
  return HttpResponse( html )


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
