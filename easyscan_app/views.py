# -*- coding: utf-8 -*-

import logging, os, pprint
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlquote
from easyscan_app import models
from easyscan_app.easyscan_forms import CitationForm


log = logging.getLogger(__name__)
request_view_get_helper = models.RequestViewGetHelper()
request_view_post_helper = models.RequestViewPostHelper()
# barcode_view_helper = models.BarcodeViewHelper()
shib_view_helper = models.ShibViewHelper()
confirmation_vew_helper = models.ConfirmationViewHelper()


def info( request ):
    """ Returns info page. """
    return render( request, u'easyscan_app_templates/info.html' )


def easyscan_js( request ):
    """ Returns javascript file.
        Will switch to direct apache serving, but this allows the 'Request Scan' link to be set dynamically, useful for testing. """
    js_unicode = u''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    js_path = u'%s/lib/josiah_easyscan.js' % current_directory
    with open( js_path ) as f:
        js_utf8 = f.read()
        js_unicode = js_utf8.decode( u'utf-8' )
    js_unicode = js_unicode.replace( u'HOST', request.get_host() )
    scheme = u'https' if request.is_secure() else u'http'
    js_unicode = js_unicode.replace( u'SCHEME', scheme )
    return HttpResponse( js_unicode, content_type = u'application/javascript; charset=utf-8' )


def request_item_js( request ):
    """ Returns javascript file.
        Will switch to direct apache serving, but this allows the 'Request Scan' link to be set dynamically, useful for testing. """
    js_unicode = u''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    js_path = u'%s/lib/josiah_request_item.js' % current_directory
    with open( js_path ) as f:
        js_utf8 = f.read()
        js_unicode = js_utf8.decode( u'utf-8' )
    js_unicode = js_unicode.replace( u'HOST', request.get_host() )
    return HttpResponse( js_unicode, content_type = u'application/javascript; charset=utf-8' )


# def request_def( request ):
#     """ On GET, redirects to login options, or displays form to specify requested scan-content.
#         On POST, saves data and redirects to confirmation page. """
#     if request.method == u'GET':
#         return_response = request_view_get_helper.handle_get( request )
#         return return_response
#     else:  # form POST
#         form = CitationForm( request.POST )
#         log.debug( u'in views.request_def() (post); form.errors, %s' % form.errors )
#         if form.is_valid():
#             log.debug( u'in views.request_def() (post); form.errors 2, %s' % form.errors )
#             request_view_post_helper.update_session( request )
#             scnrqst = request_view_post_helper.save_post_data( request )
#             request_view_post_helper.transfer_data( scnrqst )  # will eventually trigger queue job instead of sending directly
#             scheme = u'https' if request.is_secure() else u'http'
#             redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'confirmation_url') )
#             log.debug( u'in views.request_def() (post); about to redirect' )
#             return HttpResponseRedirect( redirect_url )
#         else:
#             log.debug( u'in views.request_def() (post); form.errors 3, %s' % form.errors )
#             request.session[u'form_data'] = request.POST
#             return HttpResponseRedirect( reverse(u'request_url'), {u'form': form} )


def request_def( request ):
    """ On GET, redirects to login options, or displays form to specify requested scan-content.
        On POST, saves data and redirects to confirmation page. """
    if request.method == u'GET':
        return_response = request_view_get_helper.handle_get( request )
        return return_response
    else:  # form POST
        form = CitationForm( request.POST )
        log.debug( u'in views.request_def() (post); form.errors, %s' % form.errors )
        if form.is_valid():
            log.debug( u'in views.request_def() (post); form.errors 2, %s' % form.errors )
            request_view_post_helper.update_session( request )
            scnrqst = request_view_post_helper.save_post_data( request )
            request_view_post_helper.transfer_data( scnrqst )  # will eventually trigger queue job instead of sending directly
            request_view_post_helper.email_patron( scnrqst )
            scheme = u'https' if request.is_secure() else u'http'
            redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'confirmation_url') )
            log.debug( u'in views.request_def() (post); about to redirect' )
            return HttpResponseRedirect( redirect_url )
        else:
            log.debug( u'in views.request_def() (post); form.errors 3, %s' % form.errors )
            request.session[u'form_data'] = request.POST
            return HttpResponseRedirect( reverse(u'request_url'), {u'form': form} )


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


def confirmation( request ):
    """ Logs user out & displays confirmation screen after submission.
        TODO- refactor commonalities with shib_logout() """
    try:
        barcode = request.session[u'item_info'][u'barcode']
    except:
        scheme = u'https' if request.is_secure() else u'http'
        redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'info_url') )
        return HttpResponseRedirect( redirect_url )
    if request.session[u'authz_info'][u'authorized'] == True:  # always true initially
        return_response = confirmation_vew_helper.handle_authorized( request )
    else:  # False is set by handle_authorized()
        return_response = confirmation_vew_helper.handle_non_authorized( request )
    return return_response


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
