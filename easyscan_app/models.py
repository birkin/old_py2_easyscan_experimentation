# -*- coding: utf-8 -*-

import csv, datetime, json, logging, os, pprint, StringIO
import requests
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core import serializers
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import smart_unicode
from django.utils.http import urlquote
from easyscan_app.easyscan_forms import CitationForm
from easyscan_app.lib.magic_bus import Prepper, Sender


log = logging.getLogger(__name__)
prepper = Prepper()
sender = Sender()


## db models ##


class ScanRequest( models.Model ):
    """ Contains user & item data.
        Called by RequestViewPostHelper, TryAgainHelper. """
    item_title = models.CharField( blank=True, max_length=200 )
    item_barcode = models.CharField( blank=True, max_length=50 )
    status = models.CharField( max_length=200 )
    item_callnumber = models.CharField( blank=True, max_length=200 )
    item_volume_year = models.CharField( blank=True, max_length=200 )
    item_source_url = models.TextField( blank=True )
    item_chap_vol_title = models.TextField( blank=True )
    item_page_range_other = models.TextField( blank=True )
    item_other = models.TextField( blank=True )
    patron_name = models.CharField( blank=True, max_length=100 )
    patron_barcode = models.CharField( blank=True, max_length=50 )
    patron_email = models.CharField( blank=True, max_length=100 )
    create_datetime = models.DateTimeField( auto_now_add=True, blank=True )  # blank=True for backward compatibility
    las_conversion = models.TextField( blank=True )
    status = models.CharField( blank=True, max_length=200 )
    admin_notes = models.TextField( blank=True )

    def __unicode__(self):
        return smart_unicode( u'id: %s || title: %s' % (self.id, self.item_title) , u'utf-8', u'replace' )

    def save(self):
        super( ScanRequest, self ).save() # Call the "real" save() method
        maker = LasDataMaker()
        las_string = maker.make_csv_string(
            self.create_datetime, self.patron_name, self.patron_barcode, self.patron_email, self.item_title, self.item_barcode, self.item_chap_vol_title, self.item_page_range_other, self.item_other )
        self.las_conversion = las_string
        super( ScanRequest, self ).save() # Call the "real" save() method

    def jsonify(self):
        """ Returns object data in json-compatible dict. """
        jsn = serializers.serialize( u'json', [self] )  # json string is single-item list
        lst = json.loads( jsn )
        object_dct = lst[0]
        return object_dct

    # end class ScanRequest


## non db models below  ##


class BasicAuthHelper( object ):

    def check_basic_auth( self, request ):
        """ Checks for any, and correct, http-basic-auth info, returns boolean.
            Called by views.try_again() """
        ( GOOD_USER, GOOD_PASSWORD ) = ( os.environ[u'EZSCAN__BASIC_AUTH_USERNAME'], os.environ[u'EZSCAN__BASIC_AUTH_PASSWORD'] )
        basic_auth_ok = False
        auth_info = request.META.get( u'HTTP_AUTHORIZATION', None )
        if ( auth_info and auth_info.startswith(u'Basic ') ):
            basic_info = auth_info.lstrip( u'Basic ' )
            decoded_basic_info = basic_info.decode( u'base64' )
            ( received_username, received_password ) = decoded_basic_info.rsplit( u':', 1 )   # cool; 'rsplit-1' solves problem if 'username' contains one or more colons
            if received_username == GOOD_USER and received_password == GOOD_PASSWORD:
                basic_auth_ok = True
        return basic_auth_ok

    def display_prompt( self ):
        """ Builds http-basic-auth response which brings up username/password dialog box.
            Called by views.try_again() """
        response = HttpResponse()
        response.status_code = 401
        response[u'WWW-Authenticate'] = u'Basic realm="easyscan admin try-again"'
        return response

    # end class BasicAuthHelper


class TryAgainHelper( object ):
    """ Contains helpers for views.try_again() """

    def build_response( self, request ):
        """ Builds page.
            Called by views.try_again() """
        request.session[u'try_again_page_accessed'] = True
        data_dct = self.build_data_dct( request )
        format = request.GET.get( u'format', None )
        if request.GET.get( u'format', None ) == u'json':
          jsn = json.dumps( data_dct, sort_keys=True, indent=2 )
          return_response = HttpResponse( jsn, content_type = u'application/javascript; charset=utf-8' )
        else:
            return_response = render( request, u'easyscan_app_templates/try_again.html', data_dct )
        return return_response

    def build_data_dct( self, request ):
        """ Prepares data.
            Called by build_response() """
        month_ago = datetime.date.today() - datetime.timedelta(days=30)
        entries = ScanRequest.objects.filter( create_datetime__gte=month_ago ).order_by( u'-id' )
        jsn = serializers.serialize( u'json', entries )
        lst = json.loads( jsn )
        data_dct = { u'entries': lst, u'entries_count': len( lst ) }
        log.debug( u'in models.TryAgainHelper.build_data_dct(); data_dct prepared' )
        return data_dct

    # end class TryAgainHelper


class TryAgainConfirmationHelper( object ):
    """ Contains helpers for views.try_again_confirmation() """

    def update_get_session( self, request, scan_request_id ):
        """ Sets session variables on GET.
            Called by views.try_again_confirmation() """
        request.session[u'try_again_page_accessed'] = False
        request.session[u'try_again_confirmation_page_accessed'] = True
        request.session[u'scan_request_id'] = scan_request_id
        log.debug( u'in models.TryAgainConfirmationHelper.update_get_session(); session updated' )
        return

    def build_get_data_dct( self, scan_request_id ):
        """ Prepares data.
            Called by views.try_again_confirmation() """
        entry = ScanRequest.objects.filter( id=scan_request_id ).first()
        if entry:
            jsn = serializers.serialize( u'json', [entry] )
            lst = json.loads( jsn )
            data_dct = { u'entry': lst[0] }
        else:
            data_dct = { u'entry': None }
        log.debug( u'in models.TryAgainConfirmationHelper.build_get_data_dct(); data_dct prepared' )
        return data_dct

    def build_get_response( self, request, data_dct ):
        """ Builds response.
            Called by views.try_again_confirmation() """
        format = request.GET.get( u'format', None )
        if request.GET.get( u'format', None ) == u'json':
          jsn = json.dumps( data_dct, sort_keys=True, indent=2 )
          return_response = HttpResponse( jsn, content_type = u'application/javascript; charset=utf-8' )
        else:
            return_response = render( request, u'easyscan_app_templates/try_again_confirmation.html', data_dct )
        log.debug( u'in models.TryAgainConfirmationHelper.build_get_response(); `get` response prepared' )
        return return_response

    def resubmit_request( self, request, scan_request_id ):
        """ Updates admin-note that resubmit was requested, runs resubmit, updates admin-note that resubmit was performed.
            Called by views.try_again_confirmation() """
        request.session[u'try_again_confirmation_page_accessed'] = False
        request.session[u'scan_request_id'] = None
        self.update_notes( scan_request_id, u'resubmit requested' )
        check = self.retransfer_data( scan_request_id )
        if check[u'success']:
            self.update_notes( scan_request_id, u'resubmit completed' )
        else:
            self.update_notes( scan_request_id, u'error on resubmit, `%s`' % check[u'error_message'] )
        log.debug( u'in models.TryAgainConfirmationHelper.resubmit_request(); ending' )
        return

    def update_notes( self, scan_request_id, message ):
        """ Updates admin-note with datetime stamp.
            Called by resubmit_request() """
        entry = ScanRequest.objects.get( id=scan_request_id )
        entry.admin_notes = u'%s -- %s\r || %s' % (
            unicode( datetime.datetime.now() ), message, entry.admin_notes )
        entry.save()
        return

    def retransfer_data( self, scan_request_id ):
        """ Retransfers data; sends admin email on transfer error.
            Called by resubmit_request() """
        scnrqst = ScanRequest.objects.get( id=scan_request_id )
        ( data_filename, count_filename ) = prepper.make_data_files( datetime_object=datetime.datetime.now(), data_string=scnrqst.las_conversion )
        try:
            sender.transfer_files( data_filename, count_filename )
            check = { u'success': True, u'data_filename': data_filename, u'count_filename': count_filename }
        except Exception as e:
            request_view_post_helper = RequestViewPostHelper()
            request_view_post_helper.email_admins_on_error( unicode(repr(e)) )
            check = { u'success': False, u'error_message': unicode(repr(e)) }
        log.debug( u'in models.TryAgainConfirmationHelper.retransfer_data(); check, `%s`' % pprint.pformat(check) )
        return check

    # end class TryAgainConfirmationHelper


class LasDataMaker( object ):
    """ Contains code to make comma-delimited las string.
        Called by models.ScanRequest.save() """

    def make_csv_string(
        self, date_string, patron_name, patron_barcode, patron_email, item_title, item_barcode, item_chap_vol_title, item_page_range_other, item_other ):
        """ Makes and returns csv string from database data.
            Called by models.ScanRequest.save() """
        modified_date_string = self.make_date_string( date_string )
        utf8_data_list = self.make_utf8_data_list(
            modified_date_string, item_barcode, self.strip_stuff(patron_name), patron_barcode, self.strip_stuff(item_title), patron_email, self.strip_stuff(item_chap_vol_title), self.strip_stuff(item_page_range_other), self.strip_stuff(item_other)
            )
        utf8_csv_string = self.utf8list_to_utf8csv( utf8_data_list )
        csv_string = utf8_csv_string.decode( u'utf-8' )
        return csv_string

    def make_date_string( self, datetime_object ):
        """ Will convert datetime_object to date format required by LAS.
            Example returned format, `Mon Dec 05 2014`.
            Called by make_csv_string() """
        utf8_date_string = datetime_object.strftime( u'%a %b %d %Y' )
        date_string = utf8_date_string.decode( u'utf-8' )
        return date_string

    def strip_stuff( self, var ):
        """ Replaces various characters from field.
            Called by make_csv_string() """
        updated_var = var.replace( u'"', u"'" )
        updated_var = updated_var.replace( u'\n', u' - ' )
        updated_var = updated_var.replace( u'\r', u' - ' )
        updated_var = updated_var.replace( u'`', u"'" )
        return updated_var

    def make_utf8_data_list( self, modified_date_string, item_barcode, patron_name, patron_barcode, item_title, patron_email, item_chap_vol_title, item_page_range_other, item_other ):
        """ Assembles data elements in order required by LAS.
            Called by make_csv_string() """
        utf8_data_list = [
            'item_id_not_applicable',
            item_barcode.encode( u'utf-8', u'replace' ),
            'ED',
            'QS',
            patron_name.encode( u'utf-8', u'replace' ),
            patron_barcode.encode( u'utf-8', u'replace' ),
            item_title.encode( u'utf-8', u'replace' ),
            modified_date_string.encode( u'utf-8', u'replace' ),
            'PATRON_EMAIL: `%s` -- ARTICLE-CHAPTER-TITLE: `%s` -- PAGE-RANGE: `%s` -- OTHER: `%s`' % (
                patron_email.encode(u'utf-8', u'replace'),
                item_chap_vol_title.encode(u'utf-8', u'replace'),
                item_page_range_other.encode(u'utf-8', u'replace'),
                item_other.encode(u'utf-8', u'replace'),
                )
            ]
        return utf8_data_list

    def utf8list_to_utf8csv( self, utf8_data_list ):
        """ Converts list into utf8 string.
            Called by make_csv_string()
            Note; this python2 csv module requires utf-8 strings. """
        for entry in utf8_data_list:
            if not type(entry) == str:
                raise Exception( u'entry `%s` not of type str' % unicode(repr(entry)) )
        io = StringIO.StringIO()
        writer = csv.writer( io, delimiter=',', quoting=csv.QUOTE_ALL )
        writer.writerow( utf8_data_list )
        csv_string = io.getvalue()
        io.close()
        return csv_string

    # end class LasDataMaker


class RequestViewGetHelper( object ):
    """ Contains helpers for views.request_def() for handling GET. """

    def __init__( self ):
        self.AVAILABILITY_API_URL_ROOT = os.environ[u'EZSCAN__AVAILABILITY_API_URL_ROOT']

    def handle_get( self, request ):
        """ Handles request-page GET; returns response.
            Called by views.request_def() """
        log.debug( u'in models.RequestViewGetHelper.handle_get(); referrer, `%s`' % request.META.get(u'HTTP_REFERER', u'not_in_request_meta'), )
        self.store_remote_source_url( request )
        https_check = self.check_https( request.is_secure(), request.get_host(), request.get_full_path() )
        if https_check[u'is_secure'] == False:
            return HttpResponseRedirect( https_check[u'redirect_url'] )
        title = self.check_title( request )
        self.initialize_session( request, title )
        return_response = self.build_response( request )
        log.debug( u'in models.RequestViewGetHelper.handle_get(); returning' )
        return return_response

    def store_remote_source_url( self, request ):
        """ Stores http-refferer if from external domain.
            Called by handle_get() """
        log.debug( u'in models.RequestViewGetHelper.store_remote_source_url(); referrer, `%s`' % request.META.get(u'HTTP_REFERER', u'not_in_request_meta'), )
        remote_referrer = request.META.get( u'HTTP_REFERER', u'' )
        if not request.get_host() in remote_referrer:  # ignore same-domain and shib redirects
            if not u'sso.brown.edu' in remote_referrer:
                request.session[u'last_remote_referrer'] = remote_referrer
        log.debug( u'in models.RequestViewGetHelper.store_remote_source_url(); session items, `%s`' % pprint.pformat(request.session.items()) )
        return

    def check_https( self, is_secure, get_host, full_path ):
        """ Checks for https; returns dict with result and redirect-url.
            Called by handle_get() """
        if (is_secure == False) and (get_host != u'127.0.0.1'):
            redirect_url = u'https://%s%s' % ( get_host, full_path )
            return_dict = { u'is_secure': False, u'redirect_url': redirect_url }
        else:
            return_dict = { u'is_secure': True, u'redirect_url': u'N/A' }
        log.debug( u'in models.RequestViewGetHelper.check_https(); return_dict, `%s`' % return_dict )
        return return_dict

    def check_title( self, request ):
        """ Grabs and returns title from the availability-api if needed.
            Called by handle_get() """
        title = request.GET.get( u'title', u'' )
        if title == u'null' or title == u'':
            try: title = request.session[u'item_info'][u'title']
            except: pass
        if title == u'null' or title == u'':
            bibnum = request.GET.get( u'bibnum', u'' )
            if len( bibnum ) == 8:
                title = self.hit_availability_api( bibnum )
        log.debug( u'in models.RequestViewGetHelper.check_title(); title, %s' % title )
        return title

    def hit_availability_api( self, bibnum ):
        """ Hits availability-api with bib for title.
            Called by check_title() """
        try:
            availability_api_url = u'%s/bib/%s' % ( self.AVAILABILITY_API_URL_ROOT, bibnum )
            r = requests.get( availability_api_url )
            d = r.json()
            title = d[u'response'][u'backend_response'][0][u'title']
        except Exception as e:
            log.debug( u'in models.RequestViewGetHelper.hit_availability_api(); exception, %s' % unicode(repr(e)) )
            title = u''
        return title

    def initialize_session( self, request, title ):
        """ Initializes session vars if needed.
            Called by handle_get() """
        log.debug( u'in models.RequestViewGetHelper.initialize_session(); session items, `%s`' % pprint.pformat(request.session.items()) )
        if not u'authz_info' in request.session:
            request.session[u'authz_info'] = { u'authorized': False }
        if not u'user_info' in request.session:
            request.session[u'user_info'] = { u'name': u'', u'patron_barcode': u'', u'email': u'' }
        self.update_session_iteminfo( request, title )
        if not u'shib_login_error' in request.session:
            request.session[u'shib_login_error'] = False
        log.debug( u'in models.RequestViewGetHelper.initialize_session(); session initialized' )
        return

    def update_session_iteminfo( self, request, title ):
        """ Updates 'item_info' session key data.
            Called by initialize_session() """
        if not u'item_info' in request.session:
            request.session[u'item_info'] = {
            u'callnumber': u'', u'barcode': u'', u'title': u'', u'volume_year': u'', u'article_chapter_title': u'', u'page_range': u'', u'other': u'' }
        for key in [ u'callnumber', u'barcode', u'volume_year' ]:  # ensures new url always updates session
            value = request.GET.get( key, u'' )
            if value:
                request.session[u'item_info'][key] = value
        request.session[u'item_info'][u'item_source_url'] = request.session.get( u'last_remote_referrer', u'not_in_request_meta' )
        request.session[u'item_info'][u'title'] = title
        log.debug( u'in models.RequestViewGetHelper.update_session_iteminfo(); request.session["item_info"], `%s`' % pprint.pformat(request.session[u'item_info']) )
        return

    def build_response( self, request ):
        """ Builds response.
            Called by handle_get() """
        if request.session[u'item_info'][u'barcode'] == u'':
            return_response = HttpResponseRedirect( reverse(u'info_url') )
        elif request.session[u'authz_info'][u'authorized'] == False:
            return_response = render( request, u'easyscan_app_templates/request_login.html', self.build_data_dict(request) )
        else:
            return_response = self.handle_good_get( request )
        log.debug( u'in models.RequestViewGetHelper.build_response(); returning' )
        return return_response

    def handle_good_get( self, request ):
        """ Builds response on good get.
            Called by build_response() """
        data_dict = self.build_data_dict( request )
        form_data = request.session.get( u'form_data', None )
        form = CitationForm( form_data )
        form.is_valid() # to get errors in form
        data_dict[u'form'] = form
        return_response = render( request, u'easyscan_app_templates/request_form.html', data_dict )
        return return_response

    def build_data_dict( self, request ):
        """ Builds and returns data-dict for request page.
            Called by handle_good_get() """
        context = {
            u'title': request.session[u'item_info'][u'title'],
            u'callnumber': request.session[u'item_info'][u'callnumber'],
            u'barcode': request.session[u'item_info'][u'barcode'],
            u'volume_year': request.session[u'item_info'][u'volume_year'],
            u'login_error': request.session[u'shib_login_error'],
            }
        if request.session[u'authz_info'][u'authorized']:
            context[u'patron_name'] = request.session[u'user_info'][u'name']
            context[u'logout_url'] = reverse( u'logout_url' )
        log.debug( u'in models.RequestViewGetHelper.build_data_dict(); return_dict, `%s`' % pprint.pformat(context) )
        return context

    # end class RequestViewGetHelper


class RequestViewPostHelper( object ):
    """ Contains helpers for views.request_def() for handling POST. """

    def __init__( self ):
        self.EMAIL_FROM = os.environ[u'EZSCAN__EMAIL_FROM']
        self.EMAIL_REPLY_TO = os.environ[u'EZSCAN__EMAIL_REPLY_TO']
        self.EMAIL_GENERAL_HELP = os.environ[u'EZSCAN__EMAIL_GENERAL_HELP']
        self.PHONE_GENERAL_HELP = os.environ[u'EZSCAN__PHONE_GENERAL_HELP']
        self.ON_ERROR_EMAIL_FROM = os.environ[u'EZSCAN__ON_ERROR_EMAIL_FROM']
        self.ON_ERROR_EMAIL_TO = json.loads( os.environ[u'EZSCAN__ON_ERROR_EMAIL_TO'] )  # list

    def handle_valid_form( self, request ):
        """ Handles request page POST if form is valid.
            Called by views.request_def() """
        log.debug( u'in models.RequestViewPostHelper.handle_valid_form(); starting' )
        self.update_session( request )
        scnrqst = self.save_post_data( request )
        self.transfer_data( scnrqst )  # will eventually trigger queue job instead of sending directly
        self.email_patron( scnrqst )
        scheme = u'https' if request.is_secure() else u'http'
        redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'confirmation_url') )
        log.debug( u'in models.RequestViewPostHelper.handle_valid_form(); redirecting' )
        return redirect_url

    def update_session( self, request ):
        """ Updates session vars.
            Called by handle_valid_form() """
        request.session[u'item_info'][u'article_chapter_title'] = request.POST.get( u'article_chapter_title'.strip(), u'' )
        request.session[u'item_info'][u'page_range'] = request.POST.get( u'page_range'.strip(), u'' )
        request.session[u'item_info'][u'other'] = request.POST.get( u'other'.strip(), u'' )
        return

    def save_post_data( self, request ):
        """ Saves posted data to db.
            Called by handle_valid_form() """
        scnrqst = None
        try:
            scnrqst = ScanRequest()
            scnrqst.item_title = request.session[u'item_info'][u'title']
            scnrqst.item_barcode = request.session[u'item_info'][u'barcode']
            scnrqst.status = u'in_process'
            scnrqst.item_callnumber = request.session[u'item_info'][u'callnumber']
            scnrqst.item_volume_year = request.session[u'item_info'][u'volume_year']
            scnrqst.item_chap_vol_title = request.session[u'item_info'][u'article_chapter_title']
            scnrqst.item_page_range_other = request.session[u'item_info'][u'page_range']
            scnrqst.item_other = request.session[u'item_info'][u'other']
            scnrqst.item_source_url = request.session[u'item_info'][u'item_source_url']
            scnrqst.patron_name = request.session[u'user_info'][u'name']
            scnrqst.patron_barcode = request.session[u'user_info'][u'patron_barcode']
            scnrqst.patron_email = request.session[u'user_info'][u'email']
            scnrqst.save()
        except Exception as e:
            log.debug( u'in models.RequestViewPostHelper.save_post_data(); exception, `%s`' % unicode(repr(e)) )
        return scnrqst

    def transfer_data( self, scnrqst ):
        """ Transfers data.
            Called by handle_valid_form() """
        ( data_filename, count_filename ) = prepper.make_data_files( datetime_object=scnrqst.create_datetime, data_string=scnrqst.las_conversion )
        try:
            sender.transfer_files( data_filename, count_filename )
            scnrqst.status = u'transferred'
            scnrqst.save()
            log.debug( u'in models.RequestViewPostHelper.transfer_data(); `%s` and `%s` transferred' % (data_filename, count_filename) )
        except Exception as e:
            error_message = unicode( repr(e) )
            log.error( u'in models.RequestViewPostHelper.transfer_data(); error, `%s`' % error_message )
            self.email_admins_on_error( error_message )
        return

    def email_patron( self, scnrqst ):
        """ Emails patron confirmation.
            Called by handle_valid_form() """
        try:
            subject = u'Brown University Library - Scan Request Confirmation'
            body = self.build_email_body( scnrqst )
            ffrom = self.EMAIL_FROM  # `from` reserved
            to = [ scnrqst.patron_email ]
            extra_headers = { u'Reply-To': self.EMAIL_REPLY_TO }
            email = EmailMessage( subject, body, ffrom, to, headers=extra_headers )
            email.send()
            log.debug( u'in models.RequestViewPostHelper.email_patron(); mail sent' )
        except Exception as e:
            log.debug( u'in models.RequestViewPostHelper.email_patron(); exception, `%s`' % unicode(repr(e)) )
        return

    def build_email_body( self, scnrqst ):
        """ Prepares and returns email body.
            Called by email_patron().
            TODO: use render_to_string & template. """
        body = u'''Greetings %s,

This is a confirmation of your easyscan request for the item...

Article/Chapter title: %s
Page range: %s
Other: %s

from

Item title: %s
Volume/Year: %s

Scans generally take two business days, and will be sent to this email address.

If you have questions, feel free to email %s or call %s, and reference easyscan item_barcode '%s' and request #'%s'.''' % (
            scnrqst.patron_name,
            scnrqst.item_chap_vol_title, scnrqst.item_page_range_other, scnrqst.item_other,
            scnrqst.item_title, scnrqst.item_volume_year,
            self.EMAIL_GENERAL_HELP, self.PHONE_GENERAL_HELP, scnrqst.item_barcode, scnrqst.id
            )
        return body

    def email_admins_on_error( self, error_message ):
        """ Emails admins error.
            Called by transfer_data() """
        try:
            subject = u'easyscan error'
            body = u'Error transferring data to Annex server: `%s`' % error_message
            ffrom = self.ON_ERROR_EMAIL_FROM  # `from` reserved
            to = self.ON_ERROR_EMAIL_TO  # list
            # extra_headers = { u'Reply-To': self.EMAIL_REPLY_TO }
            # email = EmailMessage( subject, body, ffrom, to, headers=extra_headers )
            email = EmailMessage( subject, body, ffrom, to )
            email.send()
            log.debug( u'in models.RequestViewPostHelper.email_admins_on_error(); mail sent' )
        except Exception as e:
            log.debug( u'in models.RequestViewPostHelper.email_admins_on_error(); exception, `%s`' % unicode(repr(e)) )
        return

    # end class RequestViewPostHelper


class ShibViewHelper( object ):
    """ Contains helpers for views.shib_login() """

    def check_shib_headers( self, request ):
        """ Grabs and checks shib headers, returns boolean.
            Called by views.shib_login() """
        shib_checker = ShibChecker()
        shib_dict = shib_checker.grab_shib_info( request )
        validity = shib_checker.evaluate_shib_info( shib_dict )
        log.debug( u'in models.ShibViewHelper.check_shib_headers(); returning validity `%s`' % validity )
        return ( validity, shib_dict )

    def build_response( self, request, validity, shib_dict ):
        """ Sets session vars and redirects to the request page,
              which will show the citation form on login-success, and a helpful error message on login-failure.
            Called by views.shib_login() """
        self.update_session( request, validity, shib_dict )
        scheme = u'https' if request.is_secure() else u'http'
        redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'request_url') )
        return_response = HttpResponseRedirect( redirect_url )
        log.debug( u'in models.ShibViewHelper.build_response(); returning response' )
        return return_response

    def update_session( self, request, validity, shib_dict ):
        request.session[u'shib_login_error'] = validity  # boolean
        request.session[u'authz_info'][u'authorized'] = validity
        if validity:
            request.session[u'user_info'] = {
                u'name': u'%s %s' % ( shib_dict[u'firstname'], shib_dict[u'lastname'] ),
                u'email': shib_dict[u'email'],
                u'patron_barcode': shib_dict[u'patron_barcode'] }
            request.session[u'shib_login_error'] = False
        return

    # end class ShibViewHelper


class ShibChecker( object ):
    """ Contains helpers for checking Shib.
        Called by ShibViewHelper """

    def __init__( self ):
        self.TEST_SHIB_JSON = os.environ.get( u'EZSCAN__TEST_SHIB_JSON', u'' )
        self.SHIB_ERESOURCE_PERMISSION = os.environ[u'EZSCAN__SHIB_ERESOURCE_PERMISSION']

    def grab_shib_info( self, request ):
        """ Grabs shib values from http-header or dev-settings.
            Called by models.ShibViewHelper.check_shib_headers() """
        shib_dict = {}
        if u'Shibboleth-eppn' in request.META:
            shib_dict = self.grab_shib_from_meta( request )
        else:
            if request.get_host() == u'127.0.0.1' and project_settings.DEBUG == True:
                shib_dict = json.loads( self.TEST_SHIB_JSON )
        log.debug( u'in models.ShibChecker.grab_shib_info(); shib_dict is: %s' % pprint.pformat(shib_dict) )
        return shib_dict

    def grab_shib_from_meta( self, request ):
        """ Extracts shib values from http-header.
            Called by grab_shib_info() """
        shib_dict = {
            u'eppn': request.META.get( u'Shibboleth-eppn', u'' ),
            u'firstname': request.META.get( u'Shibboleth-givenName', u'' ),
            u'lastname': request.META.get( u'Shibboleth-sn', u'' ),
            u'email': request.META.get( u'Shibboleth-mail', u'' ).lower(),
            u'patron_barcode': request.META.get( u'Shibboleth-brownBarCode', u'' ),
            u'member_of': request.META.get( u'Shibboleth-isMemberOf', u'' ) }
        return shib_dict

    def evaluate_shib_info( self, shib_dict ):
        """ Returns boolean.
            Called by models.ShibViewHelper.check_shib_headers() """
        validity = False
        if self.all_values_present(shib_dict) and self.brown_user_confirmed(shib_dict) and self.eresources_allowed(shib_dict):
            validity = True
        log.debug( u'in models.ShibChecker.evaluate_shib_info(); validity, `%s`' % validity )
        return validity

    def all_values_present( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        present_check = False
        if sorted( shib_dict.keys() ) == [u'email', u'eppn', u'firstname', u'lastname', u'member_of', u'patron_barcode']:
            value_test = u'init'
            for (key, value) in shib_dict.items():
                if len( value.strip() ) == 0:
                    value_test = u'fail'
            if value_test == u'init':
                present_check = True
        log.debug( u'in models.ShibChecker.all_values_present(); present_check, `%s`' % present_check )
        return present_check

    def brown_user_confirmed( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        brown_check = False
        if u'@brown.edu' in shib_dict[u'eppn']:
            brown_check = True
        log.debug( u'in models.ShibChecker.brown_user_confirmed(); brown_check, `%s`' % brown_check )
        return brown_check

    def eresources_allowed( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        eresources_check = False
        if self.SHIB_ERESOURCE_PERMISSION in shib_dict[u'member_of']:
            eresources_check = True
        log.debug( u'in models.ShibChecker.eresources_allowed(); eresources_check, `%s`' % eresources_check )
        return eresources_check

    # end class ShibChecker


class ConfirmationViewHelper( object ):
    """ Container for views.confirmation() helpers.
        TODO- refactor commonalities with shib_logout. """

    def __init__( self ):
        self.SHIB_LOGOUT_URL_ROOT = os.environ[u'EZSCAN__SHIB_LOGOUT_URL_ROOT']
        self.EMAIL_GENERAL_HELP = os.environ[u'EZSCAN__EMAIL_GENERAL_HELP']
        self.PHONE_GENERAL_HELP = os.environ[u'EZSCAN__PHONE_GENERAL_HELP']

    def handle_authorized( self, request ):
        """ Unsets authorization, hits idp-logout, & redirects back to confirmation page.
            Called by views.confirmation() """
        request.session[u'authz_info'][u'authorized'] = False
        if request.get_host() == u'127.0.0.1' and project_settings.DEBUG == True:
            return_response = HttpResponseRedirect( reverse(u'confirmation_url') )
        else:
            scheme = u'https' if request.is_secure() else u'http'
            target_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'confirmation_url') )
            encoded_target_url =  urlquote( target_url )
            redirect_url = u'%s?return=%s' % ( os.environ[u'EZSCAN__SHIB_LOGOUT_URL_ROOT'], encoded_target_url )
            return_response = HttpResponseRedirect( redirect_url )
        return return_response

    def handle_non_authorized( self, request ):
        """ Clears session and displays confirmation page.
            (Authorization is unset by initial confirmation-page access.)
            Called by views.confirmation() """
        data_dict = {
            u'title': request.session[u'item_info'][u'title'],
            u'callnumber': request.session[u'item_info'][u'callnumber'],
            u'barcode': request.session[u'item_info'][u'barcode'],
            u'chap_vol_title': request.session[u'item_info'][u'article_chapter_title'],
            u'page_range': request.session[u'item_info'][u'page_range'],
            u'other': request.session[u'item_info'][u'other'],
            u'volume_year': request.session[u'item_info'][u'volume_year'],
            u'email': request.session[u'user_info'][u'email'],
            u'email_general_help': self.EMAIL_GENERAL_HELP,
            u'phone_general_help': self.PHONE_GENERAL_HELP
            }
        logout( request )
        return_response = render( request, u'easyscan_app_templates/confirmation_form.html', data_dict )
        return return_response

    # end class ConfirmationViewHelper


class StatsBuilder( object ):
    """ Handles stats-api calls. """

    def __init__( self ):
        self.date_start = None  # set by check_params()
        self.date_end = None  # set by check_params()
        self.output = None  # set by check_params() or...

    def check_params( self, get_params, server_name ):
        """ Checks parameters; returns boolean.
            Called by views.stats_v1() """
        log.debug( u'get_params, `%s`' % get_params )
        if u'start_date' not in get_params or u'end_date' not in get_params:  # not valid
            self._handle_bad_params( server_name )
            return False
        else:  # valid
            self.date_start = u'%s 00:00:00' % get_params[u'start_date']
            self.date_end = u'%s 23:59:59' % get_params[u'end_date']
            return True

    def run_query( self ):
        """ Queries db.
            Called by views.stats_v1() """
        requests = ScanRequest.objects.filter(
            create_datetime__gte=self.date_start).filter(create_datetime__lte=self.date_end)
        return requests

    def process_results( self, requests ):
        """ Extracts desired data from resultset.
            Called by views.stats_v1() """
        data = { u'count_request_for_period': len(requests) }
        for request in requests:
            # TODO: add in 'source'
            pass
        return data

    def build_response( self, data ):
        """ Builds json response.
            Called by views.stats_v1() """
        jdict = {
            u'request': {
                u'date_begin': self.date_start, u'date_end': self.date_end },
            u'response': {
                u'count_total': data[u'count_request_for_period'] }
            }
        self.output = json.dumps( jdict, sort_keys=True, indent=2 )
        return

    def _handle_bad_params( self, server_name ):
        """ Prepares bad-parameters data.
            Called by check_params() """
        data = {
          u'request': { u'url': reverse( u'stats_v1_url' ) },
          u'response': {
            u'status': u'400 / Bad Request',
            u'message': u'example url: https://%s/easyscan/stats_api/v1/?start_date=2015-04-01&end_date=2015-04-30' % server_name,
            }
          }
        self.output = json.dumps( data, sort_keys=True, indent=2 )
        return

    # end class StatsBuilder
