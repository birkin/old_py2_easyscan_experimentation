# -*- coding: utf-8 -*-

import logging
from django.db import models


log = logging.getLogger(__name__)


class RequestValidator( object ):
    """ Container for request-validation helpers.
        Non-django, plain-python model. """

    def check_https( self, is_secure, get_host, full_path ):
        """ Checks for https; returns dict with result and redirect-url.
            Called by views.request_def() """
        if (is_secure == False) and (get_host != u'127.0.0.1'):
            redirect_url = redirect_url = u'https://%s%s' % ( get_host, full_path )
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
