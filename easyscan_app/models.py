# -*- coding: utf-8 -*-

import logging
from django.db import models


log = logging.getLogger(__name__)


class RequestValidator( object ):
    """ Container for request-validation helpers.
        Non-django, plain-python model. """

    # def __init__( self ):
    #     """ Settings. """

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
