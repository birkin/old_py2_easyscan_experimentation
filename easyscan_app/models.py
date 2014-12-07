# -*- coding: utf-8 -*-

import logging, os, pprint
import requests
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import smart_unicode


log = logging.getLogger(__name__)


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


## non db models below  ##


class RequestViewHelper( object ):
    """ Container for views.request_def() helpers.
        Non-django, plain-python model. """

    def check_https( self, is_secure, get_host, full_path ):
        """ Checks for https; returns dict with result and redirect-url.
            Called by views.request_def() """
        if (is_secure == False) and (get_host != u'127.0.0.1'):
            redirect_url = u'https://%s%s' % ( get_host, full_path )
            return_dict = { u'is_secure': False, u'redirect_url': redirect_url }
        else:
            return_dict = { u'is_secure': True, u'redirect_url': u'N/A' }
        log.debug( u'in RequestValidator.check_https(); return_dict, `%s`' % return_dict )
        return return_dict

    def initialize_session( self, request ):
        """ Initializes session vars if needed.
            Called by views.request_def() """
        if not u'authz_info' in request.session:
            request.session[u'authz_info'] = { u'authorized': False }
        if not u'user_info' in request.session:
            request.session[u'user_info'] = { u'name': u'', u'patron_barcode': u'', u'email': u'' }
        if not u'item_info' in request.session:
            request.session[u'item_info'] = { u'callnumber': u'', u'barcode': u'', u'title': u'' }
        for key in [ u'callnumber', u'barcode', u'title' ]:  # ensures new url always updates session
            value = request.GET.get( key, u'' )
            if value:
                request.session[u'item_info'][key] = value
        if not u'barcode_login_info' in request.session:
            request.session[u'barcode_login_info'] = { u'name': u'', u'error': u'' }
        else:
            request.session[u'barcode_login_info'][u'error'] = u''
        log.debug( u'in RequestViewHelper.initialize_session(); request.session[item_info], `%s`' % pprint.pformat(request.session[u'item_info']) )
        return

    def build_data_dict( self, request ):
        """ Builds and returns data-dict for request page.
            Called by views.request_def() """
        context = {
            u'title': request.session[u'item_info'][u'title'],
            u'callnumber': request.session[u'item_info'][u'callnumber'],
            u'barcode': request.session[u'item_info'][u'barcode']
            }
        log.debug( u'in RequestPageHelper.build_data_dict(); return_dict, `%s`' % pprint.pformat(context) )
        return context


class BarcodeViewHelper( object ):
    """ Container for views.barcode_login() helpers.
        Non-django, plain-python model. """

    def handle_post( self, request ):
        """ Evaluates barcode-page POST; returns response.
            Called by views.barcode_login() """
        ( barcode_check, barcode_validator ) = ( u'init', BarcodeValidator() )
        request.session[u'barcode_login_info'][u'name'] = request.POST.get( u'name'.strip(), u'' )
        log.debug( u'in BarcodeViewHelper.handle_post(); request.session[barcode_login_info] after name inserted, `%s`' % request.session[u'barcode_login_info'] )
        barcode_check = barcode_validator.check_barcode( request.POST.get(u'patron_barcode', u''), request.session[u'barcode_login_info'][u'name'] )
        scheme = u'https' if request.is_secure() else u'http'
        if barcode_check[u'validity'] == u'valid':
            request.session[u'authz_info'][u'authorized'] = True
            request.session[u'user_info'] = {
                u'name': barcode_check[u'name'], u'patron_barcode': request.POST.get(u'patron_barcode', u''), u'email': barcode_check[u'email'] }
            request.session[u'barcode_login_info'][u'name'] = u''
            request.session[u'barcode_login_info'][u'error'] = u''
            redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'request_url') )
        else:
            log.debug( u'in BarcodeViewHelper.handle_post(); about to update session object with error string' )
            request.session[u'barcode_login_info'][u'error'] = u'Login not valid; please try again, or contact the Library for assistance.'
            redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'barcode_login_url') )
        log.debug( u'in BarcodeViewHelper.handle_post(); request.session[barcode_login_info] after error inserted, `%s`' % request.session[u'barcode_login_info'] )
        log.debug( u'in BarcodeViewHelper.handle_post(); redirect_url, `%s`' % redirect_url )
        return_response = HttpResponseRedirect( redirect_url )
        log.debug( u'in BarcodeViewHelper.handle_post(); returning' )
        return return_response


class BarcodeValidator( object ):
    """ Container for helpers to check submitted patron barcode & name.
        Non-django, plain-python model. """

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
            evaluation_dict = { u'validity': u'valid', u'name': name, u'email': parsed_data[u'email'] }
        else:
            evaluation_dict = { u'validity': u'invalid' }
        log.debug( u'in BarcodeValidator.evaluate_parsed_data(); evaluation_dict, `%s`' % evaluation_dict )
        return evaluation_dict
