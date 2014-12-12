# -*- coding: utf-8 -*-

import csv, datetime, json, logging, os, pprint, StringIO
import requests
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import smart_unicode
from django.conf import settings as project_settings
from easyscan_app.lib.magic_bus import Prepper, Sender


log = logging.getLogger(__name__)
prepper = Prepper()
sender = Sender()


## db models ##


class ScanRequest( models.Model ):
    """ Contains user & item data. """
    item_title = models.CharField( blank=True, max_length=200 )
    item_barcode = models.CharField( blank=True, max_length=50 )
    item_callnumber = models.CharField( blank=True, max_length=200 )
    item_custom_info = models.TextField( blank=True )
    patron_name = models.CharField( blank=True, max_length=100 )
    patron_barcode = models.CharField( blank=True, max_length=50 )
    patron_email = models.CharField( blank=True, max_length=100 )
    create_datetime = models.DateTimeField( auto_now_add=True, blank=True )  # blank=True for backward compatibility
    las_conversion = models.TextField( blank=True )

    def __unicode__(self):
        return smart_unicode( u'patbar%s_itmbar%s' % (self.patron_barcode, self.item_barcode) , u'utf-8', u'replace' )

    def save(self):
        super( ScanRequest, self ).save() # Call the "real" save() method
        maker = LasDataMaker()
        las_string = maker.make_csv_string(
            self.item_barcode, self.patron_name, self.patron_barcode, self.item_title, self.create_datetime, self.item_custom_info )
        self.las_conversion = las_string
        super( ScanRequest, self ).save() # Call the "real" save() method


## non db models below  ##


class LasDataMaker( object ):
    """ Container for code to make comma-delimited las string. """

    def make_csv_string(
        self, item_barcode, patron_name, patron_barcode, item_title, date_string, item_custom_info ):
        """ Makes and returns csv string from database data.
            Called by models.ScanRequest.save() """
        modified_date_string = self.make_date_string( date_string )
        utf8_data_list = self.make_utf8_data_list(
            modified_date_string, item_barcode, patron_name, patron_barcode, item_title, item_custom_info )
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

    def make_utf8_data_list( self, modified_date_string, item_barcode, patron_name, patron_barcode, item_title, item_custom_info ):
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
            item_custom_info.encode( u'utf-8', u'replace' ), ]
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


class RequestViewGetHelper( object ):
    """ Container for views.request_def() helpers for handling GET. """

    def handle_get( self, request ):
        """ Handles request-page GET; returns response. """
        https_check = self.check_https( request.is_secure(), request.get_host(), request.get_full_path() )
        if https_check[u'is_secure'] == False:
            return_response = HttpResponseRedirect( https_check[u'redirect_url'] )
            return return_response
        self.initialize_session( request )
        if request.session[u'authz_info'][u'authorized'] == False:
            return_response = render( request, u'easyscan_app_templates/request_login.html', self.build_data_dict(request) )
        else:
            return_response = render( request, u'easyscan_app_templates/request_form.html', self.build_data_dict(request) )
        log.debug( u'in models.RequestViewGetHelper.handle_get(); returning' )
        return return_response

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

    def initialize_session( self, request ):
        """ Initializes session vars if needed.
            Called by handle_get() """
        if not u'authz_info' in request.session:
            request.session[u'authz_info'] = { u'authorized': False }
        if not u'user_info' in request.session:
            request.session[u'user_info'] = { u'name': u'', u'patron_barcode': u'', u'email': u'' }
        self.update_session_iteminfo( request )
        # self.update_session_barcodelogininfo( request )
        if not u'shib_login_error' in request.session:
            request.session[u'shib_login_error'] = False
        log.debug( u'in models.RequestViewGetHelper.initialize_session(); session initialized' )
        return

    def update_session_iteminfo( self, request ):
        """ Updates 'item_info' session key data.
            Called by initialize_session() """
        if not u'item_info' in request.session:
            request.session[u'item_info'] = { u'callnumber': u'', u'barcode': u'', u'title': u'' }
        for key in [ u'callnumber', u'barcode', u'title' ]:  # ensures new url always updates session
            value = request.GET.get( key, u'' )
            if value:
                request.session[u'item_info'][key] = value
        log.debug( u'in models.RequestViewGetHelper.update_session_iteminfo(); request.session["item_info"], `%s`' % pprint.pformat(request.session[u'item_info']) )
        return

    # def update_session_barcodelogininfo( self, request ):
    #     """ Initializes or resets the barcode_login_info data.
    #         Called by initialize_session() """
    #     if not u'barcode_login_info' in request.session:
    #         request.session[u'barcode_login_info'] = { u'name': u'', u'error': u'' }
    #     else:
    #         request.session[u'barcode_login_info'][u'error'] = u''
    #     return

    def build_data_dict( self, request ):
        """ Builds and returns data-dict for request page.
            Called by handle_get() """
        context = {
            u'title': request.session[u'item_info'][u'title'],
            u'callnumber': request.session[u'item_info'][u'callnumber'],
            u'barcode': request.session[u'item_info'][u'barcode'],
            u'login_error': request.session[u'shib_login_error']
            }
        log.debug( u'in models.RequestViewGetHelper.build_data_dict(); return_dict, `%s`' % pprint.pformat(context) )
        return context


class RequestViewPostHelper( object ):
    """ Container for views.request_def() helpers for handling POST. """

    def update_session( self, request ):
        """ Updates session vars.
            Called by views.request_def() """
        request.session[u'authz_info'][u'authorized'] = False
        request.session[u'item_info'][u'callnumber'] = request.POST.get( u'custom_info'.strip(), u'' )
        return

    def save_post_data( self, request ):
        """ Saves posted data to db.
            Called by views.request_def() """
        scnrqst = None
        try:
            scnrqst = ScanRequest()
            scnrqst.item_title = request.session[u'item_info'][u'title']
            scnrqst.item_barcode = request.session[u'item_info'][u'barcode']
            scnrqst.item_callnumber = request.session[u'item_info'][u'callnumber']
            scnrqst.item_custom_info = u'%s -- %s' % (
                request.session[u'user_info'][u'email'], request.POST.get(u'custom_info'.strip(), u'') )
            log.debug( u'in models.RequestViewPostHelper.save_post_data(); scnrqst.item_custom_info, `%s`' % scnrqst.item_custom_info )
            scnrqst.patron_name = request.session[u'user_info'][u'name']
            scnrqst.patron_barcode = request.session[u'user_info'][u'patron_barcode']
            scnrqst.patron_email = request.session[u'user_info'][u'email']
            scnrqst.save()
        except Exception as e:
            log.debug( u'in models.RequestViewPostHelper.save_post_data(); exception, `%s`' % unicode(repr(e)) )
        return scnrqst

    def transfer_data( self, scnrqst ):
        """ Transfers data.
            Called by views.request_def() """
        ( data_filename, count_filename ) = prepper.make_data_files(
            datetime_object=scnrqst.create_datetime, data_string=scnrqst.las_conversion
            )
        sender.transfer_files( data_filename, count_filename )
        log.debug( u'in models.RequestViewPostHelper.transfer_data(); `%s` and `%s` transferred' % (data_filename, count_filename) )
        return


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
        return


class ShibChecker( object ):
    """ Contains helpers for checking Shib. """

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
            u'lastname': request.META.get( u'Shibboleth-eppn', u'' ),
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


class BarcodeViewHelper( object ):
    """ Container for views.barcode_login() helpers.
        Note -- December 2012: Turns out barcode-login not needed for scans; leaving code here a little while. """

    def build_data_dict( self, request ):
        """ Builds template-context on GET.
            Called by views.barcode_login() """
        data_dict = {
            u'title': request.session[u'item_info'][u'title'],
            u'callnumber': request.session[u'item_info'][u'callnumber'],
            u'barcode': request.session[u'item_info'][u'barcode'],
            u'login_error': request.session[u'barcode_login_info'][u'error'],
            u'login_name': request.session[u'barcode_login_info'][u'name']
            }
        return data_dict

    def handle_post( self, request ):
        """ Evaluates barcode-page POST; returns response.
            Called by views.barcode_login() """
        ( barcode_check, barcode_validator ) = ( u'init', BarcodeValidator() )
        request.session[u'barcode_login_info'][u'name'] = request.POST.get( u'name'.strip(), u'' )
        barcode_check = barcode_validator.check_barcode( request.POST.get(u'patron_barcode', u''), request.session[u'barcode_login_info'][u'name'] )
        scheme = u'https' if request.is_secure() else u'http'
        if barcode_check[u'validity'] == u'valid':
            redirect_url = self.handle_valid_barcode( request, barcode_check, scheme )
        else:
            redirect_url = self.handle_invalid_barcode( request, scheme )
        log.debug( u'in BarcodeViewHelper.handle_post(); redirect_url, `%s`' % redirect_url )
        return_response = HttpResponseRedirect( redirect_url )
        return return_response

    def handle_valid_barcode( self, request, barcode_check, scheme ):
        """ Updates session keys for valid barcode and returns redirect url to request form.
            Called by: handle_post() """
        request.session[u'authz_info'][u'authorized'] = True
        request.session[u'user_info'] = {
            u'name': barcode_check[u'name'], u'patron_barcode': request.POST.get(u'patron_barcode', u''), u'email': barcode_check[u'email'] }
        request.session[u'barcode_login_info'][u'name'] = u''
        request.session[u'barcode_login_info'][u'error'] = u''
        redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'request_url') )
        return redirect_url

    def handle_invalid_barcode( self, request, scheme ):
        """ Updates session keys for invalid barcode and returns redirect url to barcode login form.
            Called by: handle_post() """
        log.debug( u'in BarcodeViewHelper.handle_invalid_barcode(); about to update session object with error string' )
        request.session[u'barcode_login_info'][u'error'] = u'Login not valid; please try again, or contact the Library for assistance.'
        redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'barcode_login_url') )
        return redirect_url


class BarcodeValidator( object ):
    """ Container for helpers to check submitted patron barcode & name.
        Note -- December 2012: Turns out barcode-login not needed for scans; leaving code here a little while. """

    def __init__( self ):
        self.api_root_url = os.environ.get(u'EZSCAN__PATRONAPI_ROOT_URL', u'')

    def check_barcode( self, barcode, name ):
        """ Controller function: calls request, parse, and evaluate functions.
            Called by models.BarcodeViewHelper.handle_post() """
        raw_data = self.grab_raw_data( barcode )
        for condition in self.get_bad_conditions( raw_data ):
            if condition == True:
                return { u'validity': u'invalid', u'error': raw_data }
        parsed_data = self.parse_raw_data( raw_data )
        evaluation_dict = self.evaluate_parsed_data( parsed_data, name )
        log.debug( u'in BarcodeValidator.check_barcode(); returning evaluation_dict' )
        return evaluation_dict

    def grab_raw_data( self, barcode ):
        """ Hits api; returns raw data.
            Called by check_barcode() """
        try:
            url = u'%s/%s/dump' % ( self.api_root_url, barcode )
            r = requests.get( url, timeout=10 )
            raw_data = r.content.decode( u'utf-8' )
        except Exception as e:
            raw_data = u'Exception, `%s`' % unicode(repr(e))
        log.debug( u'in BarcodeValidator.grab_raw_data(); raw_data, `%s`' % raw_data )
        return raw_data

    def get_bad_conditions( self, raw_data ):
        """ Returns list of invalid conditions.
            Called by check_barcode() """
        bad_conditions = [
            ( u'403 Forbidden' in raw_data ),
            ( u'Invalid patron barcode' in raw_data ),
            ( u'Requested record not found' in raw_data ),
            ( raw_data.startswith(u'Exception') )
            ]
        log.debug( u'in BarcodeValidator.get_bad_conditions(); bad_conditions, `%s`' % bad_conditions )
        return bad_conditions

    def parse_raw_data( self, raw_data ):
        """ Extracts name and email elements from raw_data; returns dict.
            Called by check_barcode() """
        lines = raw_data.split( u'\n' )
        parsed_data = {}
        for line in lines:
            if u'PATRN NAME' in line:
                parsed_data[u'name'] = line
            if u'E-MAIL' in line:
                parsed_data[u'email'] = line
        parsed_data[u'name'] = self.parse_name( parsed_data[u'name'] )
        parsed_data[u'email'] = self.parse_email( parsed_data[u'email'] )
        log.debug( u'in BarcodeValidator.parse_raw_data(); parsed_data, `%s`' % parsed_data )
        return parsed_data

    def parse_name( self, name_line ):
        """ Takes raw name line; returns name data.
            Called by parse_raw_data() """
        start_position = len( u'PATRN NAME[pn]=' )
        end_position = name_line.find( u'<BR>' )
        name = name_line[start_position:end_position]
        log.debug( u'in BarcodeValidator.parse_name(); name, `%s`' % name )
        return name

    def parse_email( self, email_line ):
        """ Takes raw email line; returns email data.
            Called by parse_raw_data() """
        start_position = len( u'E-MAIL[pe]=' )
        end_position = email_line.find( u'<BR>' )
        email = email_line[start_position:end_position].lower()
        return email

    def evaluate_parsed_data( self, parsed_data, name ):
        """ Takes parsed_data dict and submitted name string; returns dict.
            Called by check_barcode() """
        all_parts = []
        last_first_elements = parsed_data[u'name'].split( u',' )  # 'last, first middle' becomes ['last', 'first middle']
        for element in last_first_elements:
            split_parts = element.strip().split()
            for part in split_parts: all_parts.append( part.lower() )  # all_parts becomes ['last', 'first', 'middle']
        if name.lower() in all_parts:  # the simple test
            evaluation_dict = { u'validity': u'valid', u'name': parsed_data[u'name'], u'email': parsed_data[u'email'] }
        else:
            evaluation_dict = { u'validity': u'invalid' }
        log.debug( u'in BarcodeValidator.evaluate_parsed_data(); evaluation_dict, `%s`' % evaluation_dict )
        return evaluation_dict
