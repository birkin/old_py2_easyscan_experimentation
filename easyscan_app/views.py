# -*- coding: utf-8 -*-

import logging, os, pprint
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
    if request.method == u'GET':
        request_view_helper.initialize_session( request )
        data_dict = request_view_helper.build_data_dict( request )
        log.debug( u'in request_def(); request.session[item_info], `%s`' % pprint.pformat(request.session[u'item_info']) )
        if request.session[u'authz_info'][u'authorized'] == False:
            return render( request, u'easyscan_app_templates/request_login.html', data_dict )
        else:
            return render( request, u'easyscan_app_templates/request_form.html', data_dict )
    else:  # POST of form
        ## save data here
        scnrqst = models.ScanRequest()
        scnrqst.item_title = request.session[u'item_info'][u'title']
        scnrqst.item_barcode = request.session[u'item_info'][u'barcode']
        scnrqst.item_callnumber = request.session[u'item_info'][u'callnumber']
        scnrqst.item_custom_info = request.POST.get( u'custom_info'.strip(), u'' )
        scnrqst.patron_name = request.session[u'user_info'][u'name']
        scnrqst.patron_barcode = request.session[u'user_info'][u'patron_barcode']
        scnrqst.patron_email = request.session[u'user_info'][u'email']
        scnrqst.save()
        request.session[u'authz_info'][u'authorized'] = False
        scheme = u'https' if request.is_secure() else u'http'
        redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'confirmation_url') )
        return  HttpResponseRedirect( redirect_url )


def shib_login( request ):
    log.debug( u'in shib_login()' )
    return HttpResponse( u'will handle shib-login; barcode-login has been implemented, try that for now' )


def barcode_login( request ):
    """ Displays barcode login form.
        Redirects to request form on success. """
    log.debug( u'in barcode_login(); request.session[barcode_login_info], `%s`' % pprint.pformat(request.session[u'barcode_login_info']) )
    if request.method == u'POST':
        return_response = barcode_view_helper.handle_post( request )
        return return_response
    else:
        data_dict = {
            u'title': request.session[u'item_info'][u'title'],
            u'callnumber': request.session[u'item_info'][u'callnumber'],
            u'barcode': request.session[u'item_info'][u'barcode'],
            u'login_error': request.session[u'barcode_login_info'][u'error'],
            u'login_name': request.session[u'barcode_login_info'][u'name']
            }
        log.debug( u'in barcode_login(); data_dict, `%s`' % pprint.pformat(data_dict) )
        return render( request, u'easyscan_app_templates/barcode_login.html', data_dict )


def confirmation( request ):
    data_dict = {
        u'title': request.session[u'item_info'][u'title'],
        u'callnumber': request.session[u'item_info'][u'callnumber'],
        u'barcode': request.session[u'item_info'][u'barcode'],
        u'email': request.session[u'user_info'][u'email']
        }
    return render( request, u'easyscan_app_templates/confirmation_form.html', data_dict )
