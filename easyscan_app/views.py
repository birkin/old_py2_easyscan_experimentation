# -*- coding: utf-8 -*-

import logging, os, pprint
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlquote
from easyscan_app import models


log = logging.getLogger(__name__)
request_view_get_helper = models.RequestViewGetHelper()
request_view_post_helper = models.RequestViewPostHelper()
# barcode_view_helper = models.BarcodeViewHelper()
shib_view_helper = models.ShibViewHelper()


def js( request ):
    """ Returns javascript file.
        Will switch to direct apache serving, but this allows the 'Request Scan' link to be set dynamically, useful for testing. """
    js_unicode = u''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    js_path = u'%s/lib/josiah_easyscan.js' % current_directory
    with open( js_path ) as f:
        js_utf8 = f.read()
        js_unicode = js_utf8.decode( u'utf-8' )
    js_unicode = js_unicode.replace( u'HOST', request.get_host() )
    return HttpResponse( js_unicode, content_type = u'application/javascript; charset=utf-8' )


def request_def( request ):
    """ On GET, redirects to login options, or displays form to specify requested scan-content.
        On POST, saves data and redirects to confirmation page. """
    if request.method == u'GET':
        return_response = request_view_get_helper.handle_get( request )
        return return_response
    else:  # form POST
        request_view_post_helper.update_session( request )
        scnrqst = request_view_post_helper.save_post_data( request )
        request_view_post_helper.transfer_data( scnrqst )  # will eventually trigger queue job instead of sending directly
        scheme = u'https' if request.is_secure() else u'http'
        redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'confirmation_url') )
        log.debug( u'in views.request_def() (post); about to redirect' )
        return HttpResponseRedirect( redirect_url )


def shib_login( request ):
    """ Examines shib headers, sets session-auth, & returns user to request page. """
    log.debug( u'in views.shib_login(); starting' )
    if request.method == u'POST':  # from request_login.html
        log.debug( u'in views.shib_login(); post detected' )
        return HttpResponseRedirect( os.environ[u'EZSCAN__SHIB_LOGIN_URL'] )  # forces reauth if user clicked logout link
    request.session[u'shib_login_error'] = u''  # initialization; updated when response is built
    ( validity, shib_dict ) = shib_view_helper.check_shib_headers( request )
    return_response = shib_view_helper.build_response( request, validity, shib_dict )
    log.debug( u'in views.shib_login(); about to return response' )
    return return_response


# def barcode_login( request ):
#     """ On GET, displays barcode login form.
#         On POST, redirects to request form on success, or barcode login form again on fail. """
#     if request.method == u'GET':
#         data_dict = barcode_view_helper.build_data_dict( request )
#         log.debug( u'in views.barcode_login(); data_dict, `%s`' % pprint.pformat(data_dict) )
#         return render( request, u'easyscan_app_templates/barcode_login.html', data_dict )
#     else:  # POST of form
#         return_response = barcode_view_helper.handle_post( request )
#         return return_response


def confirmation( request ):
    """ Logs user out & displays confirmation screen after submission.
        TODO- refactor commonalities with shib_logout() """
    if request.session[u'authz_info'][u'authorized'] == False:
        log.debug( u'in views.confirmation(); authorized is False' )
        data_dict = {
            u'title': request.session[u'item_info'][u'title'],
            u'callnumber': request.session[u'item_info'][u'callnumber'],
            u'barcode': request.session[u'item_info'][u'barcode'],
            u'email': request.session[u'user_info'][u'email']
            }
        logout( request )
        return render( request, u'easyscan_app_templates/confirmation_form.html', data_dict )
    else:
        log.debug( u'in views.confirmation(); authorized is True' )
        request.session[u'authz_info'][u'authorized'] = False
        if request.get_host() == u'127.0.0.1' and project_settings.DEBUG == True:
            log.debug( u'in views.confirmation(); localhost, returning current confirmation page' )
            return HttpResponseRedirect( reverse(u'confirmation_url') )
        else:
            log.debug( u'in views.confirmation(); not localhost, will hit logout url' )
            scheme = u'https' if request.is_secure() else u'http'
            target_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'confirmation_url') )
            encoded_target_url =  urlquote( target_url )
            redirect_url = u'%s?return=%s' % ( os.environ[u'EZSCAN__SHIB_LOGOUT_URL_ROOT'], encoded_target_url )
            log.debug( u'in views.confirmation(); logout redirect_url, `%s`' % redirect_url )
            return HttpResponseRedirect( redirect_url )

# def confirmation( request ):
#     """ Displays confirmation screen after submission. """
#     data_dict = {
#         u'title': request.session[u'item_info'][u'title'],
#         u'callnumber': request.session[u'item_info'][u'callnumber'],
#         u'barcode': request.session[u'item_info'][u'barcode'],
#         u'email': request.session[u'user_info'][u'email']
#         }
#     logout( request )
#     return render( request, u'easyscan_app_templates/confirmation_form.html', data_dict )


def shib_logout( request ):
    """ Clears session, hits shib logout, and redirects user to landing page. """
    request.session[u'authz_info'][u'authorized'] = False
    logout( request )
    scheme = u'https' if request.is_secure() else u'http'
    redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'request_url') )
    if request.get_host() == u'127.0.0.1' and project_settings.DEBUG == True:
        pass
    else:
        encoded_redirect_url =  urlquote( redirect_url )  # django's urlquote()
        redirect_url = u'%s?return=%s' % ( os.environ[u'EZSCAN__SHIB_LOGOUT_URL_ROOT'], encoded_redirect_url )
    log.debug( u'in vierws.shib_logout(); redirect_url, `%s`' % redirect_url )
    return HttpResponseRedirect( redirect_url )
