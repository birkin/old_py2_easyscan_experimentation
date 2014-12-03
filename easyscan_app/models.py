# -*- coding: utf-8 -*-

import logging, os
import requests
from django.db import models


log = logging.getLogger(__name__)


class RequestValidator( object ):
    """ Container for request-validation helpers.
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


class RequestPageHelper( object ):
    """ Container for request-page helpers.
        Non-django, plain-python model. """

    def build_data_dict( self, request ):
        """ Builds and returns data-dict for request page.
            Called by views.request_def() """
        context = {
            u'title': request.GET.get( u'title', u'' ),
            u'callnumber': request.GET.get( u'callnumber', u'' ),
            u'barcode': request.GET.get( u'barcode', u'' ),
            }
        log.debug( u'in RequestPageHelper.build_data_dict(); return_dict, `%s`' % context )
        return context


class BarcodeValidator( object ):
    """ Container for helpers checking submitted patron barcode & name.
        Non-django, plain-python model. """

    def __init__( self ):
        self.api_root_url = os.environ.get(u'EZSCAN__PATRONAPI_ROOT_URL', u'')

    def check_barcode( self, barcode, name ):
        """ Controller function: calls request, parse, and evaluate functions. """
        raw_data = self.grab_raw_data( barcode )
        log.debug( u'in BarcodeValidator.check_barcode(); raw_data, `%s`' % raw_data )
        if (u'403 Forbidden' in raw_data) or raw_data.startswith( u'Exception' ):
            return { u'validity': u'invalid', u'error': raw_data }
        parsed_data = self.parse_raw_data( raw_data )
        evaluation_dict = self.evaluate_parsed_data( parsed_data, name )
        return evaluation_dict

    def grab_raw_data( self, barcode ):
        try:
            url = u'%s/%s/dump' % ( self.api_root_url, barcode )
            r = requests.get( url, timeout=10 )
            raw_data = r.content.decode( u'utf-8' )
        except Exception as e:
            raw_data = u'Exception, `%s`' % unicode(repr(e))
        return raw_data

    def parse_raw_data( self, raw_data ):
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
        start_position = len( u'PATRN NAME[pn]=' )
        end_position = name_line.find( u'<BR>' )
        name = name_line[start_position:end_position]
        return name

    def parse_email( self, email_line ):
        start_position = len( u'E-MAIL[pe]=' )
        end_position = email_line.find( u'<BR>' )
        email = email_line[start_position:end_position].lower()
        return email

    def evaluate_parsed_data( self, parsed_data, name ):
        all_parts = []
        last_first_elements = parsed_data[u'name'].split( u',' )  # 'last, first middle' becomes ['last', 'first middle']
        for element in last_first_elements:
            split_parts = element.strip().split()
            for part in split_parts:
                all_parts.append( part.lower() )  # all_parts becomes ['last', 'first', 'middle']
        if name.lower() in all_parts:
            evaluation_dict = { u'validity': u'valid', u'name': name, u'email': parsed_data[u'email'] }
        else:
            evaluation_dict = { u'validity': u'invalid' }
        return evaluation_dict
