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
try_again_helper = models.TryAgainHelper()
try_again_confirmation_helper = models.TryAgainConfirmationHelper()
basic_auth_helper = models.BasicAuthHelper()


def info( request ):
    """ Returns info page. """
    context = {
        u'email_general_help': os.environ[u'EZSCAN__EMAIL_GENERAL_HELP'],
        u'phone_general_help': os.environ[u'EZSCAN__PHONE_GENERAL_HELP']
        }
    return render( request, u'easyscan_app_templates/info.html', context )


def request_def( request ):
    """ On GET, redirects to login options, or displays form to specify requested scan-content.
        On POST, saves data and redirects to confirmation page. """
    if request.method == u'GET':
        return_response = request_view_get_helper.handle_get( request )
        return return_response
    else:  # form POST
        form = CitationForm( request.POST )
        if form.is_valid():
            redirect_url = request_view_post_helper.handle_valid_form( request )
            return HttpResponseRedirect( redirect_url )
        else:
            request.session[u'form_data'] = request.POST; log.debug( u'in views.request_def(); posted form invalid' )
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
    if request.get_host() == u'127.0.0.1' and project_settings.DEBUG == True:  # eases local development
        pass
    else:
        encoded_redirect_url =  urlquote( redirect_url )  # django's urlquote()
        redirect_url = u'%s?return=%s' % ( os.environ[u'EZSCAN__SHIB_LOGOUT_URL_ROOT'], encoded_redirect_url )
    log.debug( u'in views.shib_logout(); redirect_url, `%s`' % redirect_url )
    return HttpResponseRedirect( redirect_url )


def try_again( request ):
    """ Returns `in_process` as well as recently-transferred records with a try-again button. """
    basic_auth_ok = basic_auth_helper.check_basic_auth( request )
    log.debug( u'in views.try_again(); basic_auth_ok, `%s`' % basic_auth_ok )
    if basic_auth_ok:
        return_response = try_again_helper.build_response( request )
    else:
        return_response = basic_auth_helper.display_prompt()
    return return_response


def try_again_confirmation( request, scan_request_id ):
    """ Confirms, on GET, that the user wants to try the request again.
        Performs, on POST, the transfer. """
    log.debug( u'in views.try_again_confirmation()' )
    if request.method == u'GET':
        if not request.session.get(u'try_again_page_accessed') == True:
            return HttpResponseRedirect( reverse(u'try_again_url') )
        try_again_confirmation_helper.update_get_session( request, scan_request_id )
        data_dct = try_again_confirmation_helper.build_get_data_dct( scan_request_id )
        return try_again_confirmation_helper.build_get_response( request, data_dct )
    if request.method == u'POST':
        if request.session.get(u'try_again_confirmation_page_accessed') == True:
            try_again_confirmation_helper.resubmit_request( request, scan_request_id )
        return HttpResponseRedirect( reverse(u'try_again_url') )


def easyscan_js( request ):
    """ Returns modified javascript file for development.
        Hit by a `dev_josiah_easyscan.js` url; production hits the apache-served js file. """
    js_unicode = u''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    js_path = u'%s/lib/josiah_easyscan.js' % current_directory
    with open( js_path ) as f:
        js_utf8 = f.read()
        js_unicode = js_utf8.decode( u'utf-8' )
    js_unicode = js_unicode.replace( u'library.brown.edu/easyscan/josiah_request_item.js', u'%s/easyscan/dev_josiah_request_item.js' % request.get_host() )
    js_unicode = js_unicode.replace( u'library.brown.edu', request.get_host() )
    scheme = u'https' if request.is_secure() else u'http'
    js_unicode = js_unicode.replace( u'https', scheme )
    return HttpResponse( js_unicode, content_type = u'application/javascript; charset=utf-8' )


def request_item_js( request ):
    """ Returns modified javascript file for development.
        Hit by a `dev_josiah_request_item.js` url; production hits the apache-served js file. """
    js_unicode = u''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    js_path = u'%s/lib/josiah_request_item.js' % current_directory
    with open( js_path ) as f:
        js_utf8 = f.read()
        js_unicode = js_utf8.decode( u'utf-8' )
    js_unicode = js_unicode.replace( u'library.brown.edu', request.get_host() )
    return HttpResponse( js_unicode, content_type = u'application/javascript; charset=utf-8' )
