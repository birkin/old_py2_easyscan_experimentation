# -*- coding: utf-8 -*-

from __future__ import unicode_literals

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
from easyscan_app.lib.spacer import Spacer


log = logging.getLogger(__name__)
prepper = Prepper()
sender = Sender()
spcr = Spacer()


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
        return smart_unicode( 'id: %s || title: %s' % (self.id, self.item_title) , 'utf-8', 'replace' )

    def save(self):
        super( ScanRequest, self ).save() # Call the "real" save() method
        maker = LasDataMaker()
        las_string = maker.make_csv_string(
            self.create_datetime, self.patron_name, self.patron_barcode, self.patron_email, self.item_title, self.item_barcode, self.item_chap_vol_title, self.item_page_range_other, self.item_other )
        self.las_conversion = las_string
        super( ScanRequest, self ).save() # Call the "real" save() method

    def jsonify(self):
        """ Returns object data in json-compatible dict. """
        jsn = serializers.serialize( 'json', [self] )  # json string is single-item list
        lst = json.loads( jsn )
        object_dct = lst[0]
        return object_dct

    # end class ScanRequest


## non db models below  ##


class BasicAuthHelper( object ):

    def check_basic_auth( self, request ):
        """ Checks for any, and correct, http-basic-auth info, returns boolean.
            Called by views.try_again() """
        ( GOOD_USER, GOOD_PASSWORD ) = ( unicode(os.environ['EZSCAN__BASIC_AUTH_USERNAME']), unicode(os.environ['EZSCAN__BASIC_AUTH_PASSWORD']) )
        basic_auth_ok = False
        auth_info = request.META.get( 'HTTP_AUTHORIZATION', None )
        if ( auth_info and auth_info.startswith('Basic ') ):
            basic_info = auth_info.lstrip( 'Basic ' )
            decoded_basic_info = basic_info.decode( 'base64' )
            ( received_username, received_password ) = decoded_basic_info.rsplit( ':', 1 )   # cool; 'rsplit-1' solves problem if 'username' contains one or more colons
            if received_username == GOOD_USER and received_password == GOOD_PASSWORD:
                basic_auth_ok = True
        return basic_auth_ok

    def display_prompt( self ):
        """ Builds http-basic-auth response which brings up username/password dialog box.
            Called by views.try_again() """
        response = HttpResponse()
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm="easyscan admin try-again"'
        return response

    # end class BasicAuthHelper


class TryAgainHelper( object ):
    """ Contains helpers for views.try_again() """

    def build_response( self, request ):
        """ Builds page.
            Called by views.try_again() """
        request.session['try_again_page_accessed'] = True
        data_dct = self.build_data_dct( request )
        format = request.GET.get( 'format', None )
        if request.GET.get( 'format', None ) == 'json':
          jsn = json.dumps( data_dct, sort_keys=True, indent=2 )
          return_response = HttpResponse( jsn, content_type = 'application/javascript; charset=utf-8' )
        else:
            return_response = render( request, 'easyscan_app_templates/try_again.html', data_dct )
        return return_response

    def build_data_dct( self, request ):
        """ Prepares data.
            Called by build_response() """
        month_ago = datetime.date.today() - datetime.timedelta(days=30)
        entries = ScanRequest.objects.filter( create_datetime__gte=month_ago ).order_by( '-id' )
        jsn = serializers.serialize( 'json', entries )
        lst = json.loads( jsn )
        data_dct = { 'entries': lst, 'entries_count': len( lst ) }
        log.debug( 'TryAgainHelper(); data_dct prepared' )
        return data_dct

    # end class TryAgainHelper


class TryAgainConfirmationHelper( object ):
    """ Contains helpers for views.try_again_confirmation() """

    def update_get_session( self, request, scan_request_id ):
        """ Sets session variables on GET.
            Called by views.try_again_confirmation() """
        request.session['try_again_page_accessed'] = False
        request.session['try_again_confirmation_page_accessed'] = True
        request.session['scan_request_id'] = scan_request_id
        log.debug( 'TryAgainConfirmationHelper(); session updated' )
        return

    def build_get_data_dct( self, scan_request_id ):
        """ Prepares data.
            Called by views.try_again_confirmation() """
        entry = ScanRequest.objects.filter( id=scan_request_id ).first()
        if entry:
            jsn = serializers.serialize( 'json', [entry] )
            lst = json.loads( jsn )
            data_dct = { 'entry': lst[0] }
        else:
            data_dct = { 'entry': None }
        log.debug( 'TryAgainConfirmationHelper(); data_dct prepared' )
        return data_dct

    def build_get_response( self, request, data_dct ):
        """ Builds response.
            Called by views.try_again_confirmation() """
        format = request.GET.get( 'format', None )
        if request.GET.get( 'format', None ) == 'json':
          jsn = json.dumps( data_dct, sort_keys=True, indent=2 )
          return_response = HttpResponse( jsn, content_type = 'application/javascript; charset=utf-8' )
        else:
            return_response = render( request, 'easyscan_app_templates/try_again_confirmation.html', data_dct )
        log.debug( 'TryAgainConfirmationHelper(); `get` response prepared' )
        return return_response

    def resubmit_request( self, request, scan_request_id ):
        """ Updates admin-note that resubmit was requested, runs resubmit, updates admin-note that resubmit was performed.
            Called by views.try_again_confirmation() """
        request.session['try_again_confirmation_page_accessed'] = False
        request.session['scan_request_id'] = None
        self.update_notes( scan_request_id, 'resubmit requested' )
        check = self.retransfer_data( scan_request_id )
        if check['success']:
            self.update_notes( scan_request_id, 'resubmit completed' )
        else:
            self.update_notes( scan_request_id, 'error on resubmit, `%s`' % check['error_message'] )
        log.debug( 'TryAgainConfirmationHelper(); ending' )
        return

    def update_notes( self, scan_request_id, message ):
        """ Updates admin-note with datetime stamp.
            Called by resubmit_request() """
        entry = ScanRequest.objects.get( id=scan_request_id )
        entry.admin_notes = '%s -- %s\r || %s' % (
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
            check = { 'success': True, 'data_filename': data_filename, 'count_filename': count_filename }
        except Exception as e:
            request_view_post_helper = RequestViewPostHelper()
            request_view_post_helper.email_admins_on_error( unicode(repr(e)) )
            check = { 'success': False, 'error_message': unicode(repr(e)) }
        log.debug( 'TryAgainConfirmationHelper(); check, `%s`' % pprint.pformat(check) )
        return check

    # end class TryAgainConfirmationHelper


class LasDataMaker( object ):
    """ Contains code to make comma-delimited las string.
        Called by models.ScanRequest.save() """

    def __init__( self ):
        pass

    def make_csv_string(
        self, date_string, patron_name, patron_barcode, patron_email, item_title, item_barcode, item_chap_vol_title, item_page_range_other, item_other ):
        """ Makes and returns csv string from database data.
            Called by models.ScanRequest.save() """
        modified_date_string = self.make_date_string( date_string )
        utf8_data_list = self.make_utf8_data_list(
            modified_date_string, item_barcode, self.strip_stuff(patron_name), patron_barcode, self.strip_stuff(item_title), patron_email, self.strip_stuff(item_chap_vol_title), self.strip_stuff(item_page_range_other), self.strip_stuff(item_other)
            )
        log.debug( 'LasDataMaker(); utf8_data_list, ```{0}```'.format(pprint.pformat(utf8_data_list)) )
        utf8_csv_string = self.utf8list_to_utf8csv( utf8_data_list )
        csv_unicode_string = utf8_csv_string.decode( 'utf-8' )
        return csv_unicode_string

    def make_date_string( self, datetime_object ):
        """ Will convert datetime_object to date format required by LAS.
            Example returned format, `Mon Dec 05 2014`.
            Called by make_csv_string() """
        utf8_date_string = datetime_object.strftime( '%a %b %d %Y' )
        date_string = utf8_date_string.decode( 'utf-8' )
        return date_string

    def strip_stuff( self, var ):
        """ Replaces various characters from field.
            Called by make_csv_string() """
        updated_var = var.replace( '"', "'" )
        updated_var = updated_var.replace( '\n', ' - ' )
        updated_var = updated_var.replace( '\r', ' - ' )
        updated_var = updated_var.replace( '`', "'" )
        return updated_var

    def make_utf8_data_list( self, modified_date_string, item_barcode, patron_name, patron_barcode, item_title, patron_email, item_chap_vol_title, item_page_range_other, item_other ):
        """ Assembles data elements in order required by LAS.
            Called by make_csv_string() """
        utf8_data_list = [
            'item_id_not_applicable'.encode( 'utf-8' ),
            item_barcode.encode( 'utf-8', 'replace' ),
            'ED'.encode( 'utf-8' ),
            'QS'.encode( 'utf-8' ),
            patron_name.encode( 'utf-8', 'replace' ),
            patron_barcode.encode( 'utf-8', 'replace' ),
            item_title.encode( 'utf-8', 'replace' ),
            modified_date_string.encode( 'utf-8', 'replace' ),
            self.make_notes_field( patron_email, item_chap_vol_title, item_page_range_other, item_other ).encode( 'utf-8', 'replace' )
            ]
        return utf8_data_list

    def make_notes_field( self, patron_email, item_chap_vol_title, item_page_range_other, item_other ):
        """ Assembles notes field.
            Called by make_utf8_data_list() """
        data = self.add_email( patron_email )
        data = self.add_article_chapter_title( data, item_chap_vol_title )
        data = self.add_page_range( data, item_page_range_other )
        data = self.add_other( data, item_other )
        log.debug( 'LasDataMaker(); data, ```{0}```'.format(data) )
        return data

    def add_email( self, patron_email ):
        """ Adds email.
            Called by make_utf8_notes_field() """
        line_1_start = 'PATRON_EMAIL...'
        line_1 = spcr.add_spacer( line_1_start )
        line_2_start = ' '
        line_2 = spcr.add_spacer( line_2_start )
        line_3_start = '{nrml} | {uppr}'.format( nrml=patron_email, uppr=patron_email.upper() )
        line_3 = spcr.add_spacer( line_3_start )
        line_4_start = ' '
        line_4 = spcr.add_spacer( line_4_start )
        data = line_1 + line_2 + line_3 + line_4
        log.debug( 'data, ```{0}```'.format(data) )
        return data

    def add_article_chapter_title( self, data, item_chap_vol_title ):
        """ Adds email.
            Called by make_utf8_notes_field() """
        line_1_start = 'ARTICLE-CHAPTER-TITLE...'
        line_1 = spcr.add_spacer( line_1_start )
        line_2_start = ' '
        line_2 = spcr.add_spacer( line_2_start )
        line_3_start = '{0}'.format( item_chap_vol_title )
        line_3 = spcr.add_spacer( line_3_start )
        line_4_start = ' '
        line_4 = spcr.add_spacer( line_4_start )
        data = data + line_1 + line_2 + line_3 + line_4
        log.debug( 'data, ```{0}```'.format(data) )
        return data

    # def add_article_chapter_title( self, data, item_chap_vol_title ):
    #     """ Adds email.
    #         Called by make_utf8_notes_field() """
    #     line_1_start = 'ARTICLE-CHAPTER-TITLE...'
    #     line_1 = spcr.add_spacer( line_1_start )
    #     line_2_start = '{0}'.format( item_chap_vol_title )
    #     line_2 = spcr.add_spacer( line_2_start )
    #     data = data + line_1 + line_2
    #     log.debug( 'data, ```{0}```'.format(data) )
    #     return data

    def add_page_range( self, data, item_page_range_other ):
        """ Adds page-range.
            Called by make_utf8_notes_field() """
        line_start = 'PAGE-RANGE: {0}'.format(item_page_range_other)
        line = spcr.add_spacer( line_start )
        data = data + line
        log.debug( 'data, ```{0}```'.format(data) )
        return data

    def add_other( self, data, item_other ):
        """ Adds other info.
            Called by make_utf8_notes_field() """
        line_start = 'PAGE-OTHER: {0}'.format(item_other)
        line = spcr.add_spacer( line_start )
        data = data + line
        log.debug( 'data, ```{0}```'.format(data) )
        return data

    def utf8list_to_utf8csv( self, utf8_data_list ):
        """ Converts list into utf8 string.
            Called by make_csv_string()
            Note; this python2 csv module requires utf-8 strings. """
        log.debug( 'utf8_data_list, ```{0}```'.format(pprint.pformat(utf8_data_list)) )
        for entry in utf8_data_list:
            if not type(entry) == str:
                raise Exception( 'entry `%s` not of type str' % unicode(repr(entry)) )
        io = StringIO.StringIO()
        writer = csv.writer( io, delimiter=','.encode('utf-8'), quoting=csv.QUOTE_ALL )
        writer.writerow( utf8_data_list )
        csv_string = io.getvalue()  # csv_string is a byte-string
        log.debug( 'type(csv_string), `{0}'.format( type(csv_string) ) )
        log.debug( 'csv_string, ```{0}```'.format( csv_string.decode('utf-8') ) )
        io.close()
        return csv_string

    # end class LasDataMaker


class RequestViewGetHelper( object ):
    """ Contains helpers for views.request_def() for handling GET. """

    def __init__( self ):
        self.AVAILABILITY_API_URL_ROOT = os.environ['EZSCAN__AVAILABILITY_API_URL_ROOT']

    def handle_get( self, request ):
        """ Handles request-page GET; returns response.
            Called by views.request_def() """
        log.debug( 'RequestViewGetHelper(); referrer, `%s`' % request.META.get('HTTP_REFERER', 'not_in_request_meta'), )
        self.store_remote_source_url( request )
        https_check = self.check_https( request.is_secure(), request.get_host(), request.get_full_path() )
        if https_check['is_secure'] == False:
            return HttpResponseRedirect( https_check['redirect_url'] )
        title = self.check_title( request )
        self.initialize_session( request, title )
        return_response = self.build_response( request )
        log.debug( 'RequestViewGetHelper(); returning' )
        return return_response

    def store_remote_source_url( self, request ):
        """ Stores http-refferer if from external domain.
            Called by handle_get() """
        log.debug( 'RequestViewGetHelper(); referrer, `%s`' % request.META.get('HTTP_REFERER', 'not_in_request_meta'), )
        remote_referrer = request.META.get( 'HTTP_REFERER', '' )
        if not request.get_host() in remote_referrer:  # ignore same-domain and shib redirects
            if not 'sso.brown.edu' in remote_referrer:
                request.session['last_remote_referrer'] = remote_referrer
        log.debug( 'RequestViewGetHelper(); session items, `%s`' % pprint.pformat(request.session.items()) )
        return

    def check_https( self, is_secure, get_host, full_path ):
        """ Checks for https; returns dict with result and redirect-url.
            Called by handle_get() """
        if (is_secure == False) and (get_host != '127.0.0.1'):
            redirect_url = 'https://%s%s' % ( get_host, full_path )
            return_dict = { 'is_secure': False, 'redirect_url': redirect_url }
        else:
            return_dict = { 'is_secure': True, 'redirect_url': 'N/A' }
        log.debug( 'RequestViewGetHelper(); return_dict, `%s`' % return_dict )
        return return_dict

    def check_title( self, request ):
        """ Grabs and returns title from the availability-api if needed.
            Called by handle_get() """
        title = request.GET.get( 'title', '' )
        if title == 'null' or title == '':
            try: title = request.session['item_info']['title']
            except: pass
        if title == 'null' or title == '':
            bibnum = request.GET.get( 'bibnum', '' )
            if len( bibnum ) == 8:
                title = self.hit_availability_api( bibnum )
        log.debug( 'RequestViewGetHelper(); title, %s' % title )
        return title

    def hit_availability_api( self, bibnum ):
        """ Hits availability-api with bib for title.
            Called by check_title() """
        try:
            availability_api_url = '%s/bib/%s' % ( self.AVAILABILITY_API_URL_ROOT, bibnum )
            r = requests.get( availability_api_url )
            d = r.json()
            title = d['response']['backend_response'][0]['title']
        except Exception as e:
            log.debug( 'RequestViewGetHelper(); exception, %s' % unicode(repr(e)) )
            title = ''
        return title

    def initialize_session( self, request, title ):
        """ Initializes session vars if needed.
            Called by handle_get() """
        log.debug( 'RequestViewGetHelper(); session items, `%s`' % pprint.pformat(request.session.items()) )
        if not 'authz_info' in request.session:
            request.session['authz_info'] = { 'authorized': False }
        if not 'user_info' in request.session:
            request.session['user_info'] = { 'name': '', 'patron_barcode': '', 'email': '' }
        self.update_session_iteminfo( request, title )
        if not 'shib_login_error' in request.session:
            request.session['shib_login_error'] = False
        log.debug( 'RequestViewGetHelper(); session initialized' )
        return

    def update_session_iteminfo( self, request, title ):
        """ Updates 'item_info' session key data.
            Called by initialize_session() """
        if not 'item_info' in request.session:
            request.session['item_info'] = {
            'callnumber': '', 'barcode': '', 'title': '', 'volume_year': '', 'article_chapter_title': '', 'page_range': '', 'other': '' }
        for key in [ 'callnumber', 'barcode', 'volume_year' ]:  # ensures new url always updates session
            value = request.GET.get( key, '' )
            if value:
                request.session['item_info'][key] = value
        request.session['item_info']['item_source_url'] = request.session.get( 'last_remote_referrer', 'not_in_request_meta' )
        request.session['item_info']['title'] = title
        log.debug( 'RequestViewGetHelper(); request.session["item_info"], `%s`' % pprint.pformat(request.session['item_info']) )
        return

    def build_response( self, request ):
        """ Builds response.
            Called by handle_get() """
        if request.session['item_info']['barcode'] == '':
            return_response = HttpResponseRedirect( reverse('info_url') )
        elif request.session['authz_info']['authorized'] == False:
            return_response = render( request, 'easyscan_app_templates/request_login.html', self.build_data_dict(request) )
        else:
            return_response = self.handle_good_get( request )
        log.debug( 'RequestViewGetHelper(); returning' )
        return return_response

    def handle_good_get( self, request ):
        """ Builds response on good get.
            Called by build_response() """
        data_dict = self.build_data_dict( request )
        form_data = request.session.get( 'form_data', None )
        form = CitationForm( form_data )
        form.is_valid() # to get errors in form
        data_dict['form'] = form
        return_response = render( request, 'easyscan_app_templates/request_form.html', data_dict )
        return return_response

    def build_data_dict( self, request ):
        """ Builds and returns data-dict for request page.
            Called by handle_good_get() """
        context = {
            'title': request.session['item_info']['title'],
            'callnumber': request.session['item_info']['callnumber'],
            'barcode': request.session['item_info']['barcode'],
            'volume_year': request.session['item_info']['volume_year'],
            'login_error': request.session['shib_login_error'],
            }
        if request.session['authz_info']['authorized']:
            context['patron_name'] = request.session['user_info']['name']
            context['logout_url'] = reverse( 'logout_url' )
        log.debug( 'RequestViewGetHelper(); return_dict, `%s`' % pprint.pformat(context) )
        return context

    # end class RequestViewGetHelper


class RequestViewPostHelper( object ):
    """ Contains helpers for views.request_def() for handling POST. """

    def __init__( self ):
        self.EMAIL_FROM = os.environ['EZSCAN__EMAIL_FROM']
        self.EMAIL_REPLY_TO = os.environ['EZSCAN__EMAIL_REPLY_TO']
        self.EMAIL_GENERAL_HELP = os.environ['EZSCAN__EMAIL_GENERAL_HELP']
        self.PHONE_GENERAL_HELP = os.environ['EZSCAN__PHONE_GENERAL_HELP']
        self.ON_ERROR_EMAIL_FROM = os.environ['EZSCAN__ON_ERROR_EMAIL_FROM']
        self.ON_ERROR_EMAIL_TO = json.loads( os.environ['EZSCAN__ON_ERROR_EMAIL_TO'] )  # list

    def handle_valid_form( self, request ):
        """ Handles request page POST if form is valid.
            Called by views.request_def() """
        log.debug( 'RequestViewPostHelper(); starting' )
        self.update_session( request )
        scnrqst = self.save_post_data( request )
        self.transfer_data( scnrqst )  # will eventually trigger queue job instead of sending directly
        self.email_patron( scnrqst )
        scheme = 'https' if request.is_secure() else 'http'
        redirect_url = '%s://%s%s' % ( scheme, request.get_host(), reverse('confirmation_url') )
        log.debug( 'RequestViewPostHelper(); redirecting' )
        return redirect_url

    def update_session( self, request ):
        """ Updates session vars.
            Called by handle_valid_form() """
        request.session['item_info']['article_chapter_title'] = request.POST.get( 'article_chapter_title'.strip(), b'' )
        request.session['item_info']['page_range'] = request.POST.get( 'page_range'.strip(), b'' )
        request.session['item_info']['other'] = request.POST.get( 'other'.strip(), b'' )
        log.debug( 'RequestViewPostHelper(); session-updated' )
        return

    def save_post_data( self, request ):
        """ Saves posted data to db.
            Called by handle_valid_form() """
        scnrqst = None
        try:
            scnrqst = ScanRequest()
            scnrqst.item_title = request.session['item_info']['title'].decode('utf-8')
            scnrqst.item_barcode = request.session['item_info']['barcode'].decode('utf-8')
            scnrqst.status = 'in_process'
            scnrqst.item_callnumber = request.session['item_info']['callnumber'].decode('utf-8')
            scnrqst.item_volume_year = request.session['item_info']['volume_year'].decode('utf-8')
            scnrqst.item_chap_vol_title = request.session['item_info']['article_chapter_title'].decode('utf-8')
            scnrqst.item_page_range_other = request.session['item_info']['page_range'].decode('utf-8')
            scnrqst.item_other = request.session['item_info']['other'].decode('utf-8')
            scnrqst.item_source_url = request.session['item_info']['item_source_url'].decode('utf-8')
            scnrqst.patron_name = request.session['user_info']['name'].decode('utf-8')
            scnrqst.patron_barcode = request.session['user_info']['patron_barcode'].decode('utf-8')
            scnrqst.patron_email = request.session['user_info']['email'].decode('utf-8')
            scnrqst.save()
            log.debug( 'RequestViewPostHelper(); post-data saved' )
        except Exception as e:
            log.debug( 'RequestViewPostHelper(); exception, `%s`' % unicode(repr(e)) )
        return scnrqst

    def transfer_data( self, scnrqst ):
        """ Transfers data.
            Called by handle_valid_form() """
        ( data_filename, count_filename ) = prepper.make_data_files( datetime_object=scnrqst.create_datetime, data_string=scnrqst.las_conversion )
        try:
            # log.debug( 'here-A' )
            sender.transfer_files( data_filename, count_filename )
            log.debug( 'RequestViewPostHelper(); here-B' )
            scnrqst.status = 'transferred'
            scnrqst.save()
            log.debug( 'RequestViewPostHelper(); `%s` and `%s` transferred' % (data_filename, count_filename) )
        except Exception as e:
            error_message = unicode( repr(e) )
            log.error( 'RequestViewPostHelper(); error, `%s`' % error_message )
            self.email_admins_on_error( error_message )
        return

    def email_patron( self, scnrqst ):
        """ Emails patron confirmation.
            Called by handle_valid_form() """
        try:
            subject = 'Brown University Library - Scan Request Confirmation'
            body = self.build_email_body( scnrqst )
            ffrom = self.EMAIL_FROM  # `from` reserved
            to = [ scnrqst.patron_email ]
            extra_headers = { 'Reply-To': self.EMAIL_REPLY_TO }
            email = EmailMessage( subject, body, ffrom, to, headers=extra_headers )
            email.send()
            log.debug( 'RequestViewPostHelper(); mail sent' )
        except Exception as e:
            log.debug( 'RequestViewPostHelper(); exception, `%s`' % unicode(repr(e)) )
        return

    def build_email_body( self, scnrqst ):
        """ Prepares and returns email body.
            Called by email_patron().
            TODO: use render_to_string & template. """
        body = '''Greetings %s,

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
            subject = 'easyscan error'
            body = 'Error transferring data to Annex server: `%s`' % error_message
            ffrom = self.ON_ERROR_EMAIL_FROM  # `from` reserved
            to = self.ON_ERROR_EMAIL_TO  # list
            # extra_headers = { 'Reply-To': self.EMAIL_REPLY_TO }
            # email = EmailMessage( subject, body, ffrom, to, headers=extra_headers )
            email = EmailMessage( subject, body, ffrom, to )
            email.send()
            log.debug( 'RequestViewPostHelper(); mail sent' )
        except Exception as e:
            log.debug( 'RequestViewPostHelper(); exception, `%s`' % unicode(repr(e)) )
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
        log.debug( 'ShibViewHelper(); returning validity `%s`' % validity )
        return ( validity, shib_dict )

    def build_response( self, request, validity, shib_dict ):
        """ Sets session vars and redirects to the request page,
              which will show the citation form on login-success, and a helpful error message on login-failure.
            Called by views.shib_login() """
        self.update_session( request, validity, shib_dict )
        scheme = 'https' if request.is_secure() else 'http'
        redirect_url = '%s://%s%s' % ( scheme, request.get_host(), reverse('request_url') )
        return_response = HttpResponseRedirect( redirect_url )
        log.debug( 'ShibViewHelper(); returning response' )
        return return_response

    def update_session( self, request, validity, shib_dict ):
        request.session['shib_login_error'] = validity  # boolean
        request.session['authz_info']['authorized'] = validity
        if validity:
            request.session['user_info'] = {
                'name': '%s %s' % ( shib_dict['firstname'], shib_dict['lastname'] ),
                'email': shib_dict['email'],
                'patron_barcode': shib_dict['patron_barcode'] }
            request.session['shib_login_error'] = False
        return

    # end class ShibViewHelper


class ShibChecker( object ):
    """ Contains helpers for checking Shib.
        Called by ShibViewHelper """

    def __init__( self ):
        self.TEST_SHIB_JSON = os.environ.get( 'EZSCAN__TEST_SHIB_JSON', '' )
        self.SHIB_ERESOURCE_PERMISSION = os.environ['EZSCAN__SHIB_ERESOURCE_PERMISSION']

    def grab_shib_info( self, request ):
        """ Grabs shib values from http-header or dev-settings.
            Called by models.ShibViewHelper.check_shib_headers() """
        shib_dict = {}
        if 'Shibboleth-eppn' in request.META:
            shib_dict = self.grab_shib_from_meta( request )
        else:
            if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:
                shib_dict = json.loads( self.TEST_SHIB_JSON )
        log.debug( 'ShibChecker(); shib_dict is: %s' % pprint.pformat(shib_dict) )
        return shib_dict

    def grab_shib_from_meta( self, request ):
        """ Extracts shib values from http-header.
            Called by grab_shib_info() """
        shib_dict = {
            'eppn': request.META.get( 'Shibboleth-eppn', '' ),
            'firstname': request.META.get( 'Shibboleth-givenName', '' ),
            'lastname': request.META.get( 'Shibboleth-sn', '' ),
            'email': request.META.get( 'Shibboleth-mail', '' ).lower(),
            'patron_barcode': request.META.get( 'Shibboleth-brownBarCode', '' ),
            'member_of': request.META.get( 'Shibboleth-isMemberOf', '' ) }
        return shib_dict

    def evaluate_shib_info( self, shib_dict ):
        """ Returns boolean.
            Called by models.ShibViewHelper.check_shib_headers() """
        validity = False
        if self.all_values_present(shib_dict) and self.brown_user_confirmed(shib_dict) and self.eresources_allowed(shib_dict):
            validity = True
        log.debug( 'ShibChecker(); validity, `%s`' % validity )
        return validity

    def all_values_present( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        present_check = False
        if sorted( shib_dict.keys() ) == ['email', 'eppn', 'firstname', 'lastname', 'member_of', 'patron_barcode']:
            value_test = 'init'
            for (key, value) in shib_dict.items():
                if len( value.strip() ) == 0:
                    value_test = 'fail'
            if value_test == 'init':
                present_check = True
        log.debug( 'ShibChecker(); present_check, `%s`' % present_check )
        return present_check

    def brown_user_confirmed( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        brown_check = False
        if '@brown.edu' in shib_dict['eppn']:
            brown_check = True
        log.debug( 'ShibChecker(); brown_check, `%s`' % brown_check )
        return brown_check

    def eresources_allowed( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        eresources_check = False
        if self.SHIB_ERESOURCE_PERMISSION in shib_dict['member_of']:
            eresources_check = True
        log.debug( 'ShibChecker(); eresources_check, `%s`' % eresources_check )
        return eresources_check

    # end class ShibChecker


class ConfirmationViewHelper( object ):
    """ Container for views.confirmation() helpers.
        TODO- refactor commonalities with shib_logout. """

    def __init__( self ):
        self.SHIB_LOGOUT_URL_ROOT = os.environ['EZSCAN__SHIB_LOGOUT_URL_ROOT']
        self.EMAIL_GENERAL_HELP = os.environ['EZSCAN__EMAIL_GENERAL_HELP']
        self.PHONE_GENERAL_HELP = os.environ['EZSCAN__PHONE_GENERAL_HELP']

    def handle_authorized( self, request ):
        """ Unsets authorization, hits idp-logout, & redirects back to confirmation page.
            Called by views.confirmation() """
        request.session['authz_info']['authorized'] = False
        if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:
            return_response = HttpResponseRedirect( reverse('confirmation_url') )
        else:
            scheme = 'https' if request.is_secure() else 'http'
            target_url = '%s://%s%s' % ( scheme, request.get_host(), reverse('confirmation_url') )
            encoded_target_url =  urlquote( target_url )
            redirect_url = '%s?return=%s' % ( os.environ['EZSCAN__SHIB_LOGOUT_URL_ROOT'], encoded_target_url )
            return_response = HttpResponseRedirect( redirect_url )
        return return_response

    def handle_non_authorized( self, request ):
        """ Clears session and displays confirmation page.
            (Authorization is unset by initial confirmation-page access.)
            Called by views.confirmation() """
        data_dict = {
            'title': request.session['item_info']['title'],
            'callnumber': request.session['item_info']['callnumber'],
            'barcode': request.session['item_info']['barcode'],
            'chap_vol_title': request.session['item_info']['article_chapter_title'],
            'page_range': request.session['item_info']['page_range'],
            'other': request.session['item_info']['other'],
            'volume_year': request.session['item_info']['volume_year'],
            'email': request.session['user_info']['email'],
            'email_general_help': self.EMAIL_GENERAL_HELP,
            'phone_general_help': self.PHONE_GENERAL_HELP
            }
        logout( request )
        return_response = render( request, 'easyscan_app_templates/confirmation_form.html', data_dict )
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
        log.debug( 'StatsBuilder(); get_params, `%s`' % get_params )
        if 'start_date' not in get_params or 'end_date' not in get_params:  # not valid
            self._handle_bad_params( server_name )
            return False
        else:  # valid
            self.date_start = '%s 00:00:00' % get_params['start_date']
            self.date_end = '%s 23:59:59' % get_params['end_date']
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
        data = { 'count_request_for_period': len(requests) }
        for request in requests:
            # TODO: add in 'source'
            pass
        return data

    def build_response( self, data ):
        """ Builds json response.
            Called by views.stats_v1() """
        jdict = {
            'request': {
                'date_begin': self.date_start, 'date_end': self.date_end },
            'response': {
                'count_total': data['count_request_for_period'] }
            }
        self.output = json.dumps( jdict, sort_keys=True, indent=2 )
        return

    def _handle_bad_params( self, server_name ):
        """ Prepares bad-parameters data.
            Called by check_params() """
        data = {
          'request': { 'url': reverse( 'stats_v1_url' ) },
          'response': {
            'status': '400 / Bad Request',
            'message': 'example url: https://%s/easyscan/stats_api/v1/?start_date=2015-04-01&end_date=2015-04-30' % server_name,
            }
          }
        self.output = json.dumps( data, sort_keys=True, indent=2 )
        return

    # end class StatsBuilder
