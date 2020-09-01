""""
Validates initial landing-page request.
Triggered by views.confirm()
"""

# import json, logging, os, urllib
import json, logging, os, urlparse
from django.conf import settings as project_settings
from django.http import HttpResponseBadRequest
from django.template import loader


log = logging.getLogger(__name__)


class Validator( object ):
    """ Validates source and params. """

    def __init__( self ):
        """ Holds env-vars. """
        # self.EMAIL_AUTH_HELP = os.environ['EZRQST_HAY__EMAIL_AUTH_HELP']
        self.LEGIT_SOURCES = json.loads( os.environ['EZSCAN__LEGIT_SOURCES_JSON'])

    def validate_source( self, request ):
        """ Ensures app is accessed from legit source.
            Called by views.confirm() """
        return_val = False
        # if '127.0.0.1' in request.get_host() and project_settings.DEBUG == True:
        if project_settings.DEBUG == True:
            return_val = True
        referrer_host = self.get_referrer_host( request.META.get('HTTP_REFERER', 'unavailable') )
        log.debug( 'referrer_host, `%s`' % referrer_host )
        if referrer_host in self.LEGIT_SOURCES:
            return_val = True
        log.debug( 'return_val, `%s`' % return_val )
        return return_val

    def get_referrer_host( self, referrer_url ):
        """ Extracts host from referrer_url.
            Called by validate_source() """
        output = urlparse.urlparse( referrer_url )  # python2
        # output = urllib.parse.urlparse( referrer_url )  # python3
        host = output.netloc
        log.debug( 'referrer host, `%s`' % host )
        return host

    # def validate_params( self, request ):
    #     """ Checks params.
    #         Called by views.confirm()
    #         Note: `barcode` here is the item-barcode. """
    #     return_val = False
    #     if 'item_barcode' in request.GET.keys():
    #         if 'item_bib' in request.GET.keys():
    #             # if len(request.GET['item_bib']) == 8:
    #             #     if len(request.GET['item_barcode']) == 14:
    #             if len(request.GET['item_bib']) > 0:
    #                 if len(request.GET['item_barcode']) > 0:
    #                     return_val = True
    #     log.debug( 'return_val, `%s`' % return_val )
    #     return return_val

    # def validate_confirm_handler_params( self, request ):
    #     """ Checks params.
    #         Called by views.confirm_handler() """
    #     return_val = False
    #     if 'shortlink' in request.GET.keys():
    #         return_val = True
    #     log.debug( 'return_val, `%s`' % return_val )
    #     return return_val

    def prepare_badrequest_response( self, request ):
        """ Prepares bad-request response when validation fails.
            Called by views.login() """
        message = """
<p>This webapp should be accessed directly from the scan links on search.library.brown.edu pages.</p>
<p>Example page with scan links: <a href="https://search.library.brown.edu/catalog/b1234549">https://search.library.brown.edu/catalog/b1234549</a></p>
"""
        bad_resp = HttpResponseBadRequest( message )
        log.debug( 'returning bad-request response' )
        return bad_resp

    # def prepare_badrequest_response( self, request ):
    #     """ Prepares bad-request response when validation fails.
    #         Called by views.login() """
    #     template = loader.get_template('easyrequest_hay_app_templates/problem.html')
    #     context = {
    #         'help_email': self.EMAIL_AUTH_HELP,
    #     }
    #     bad_resp = HttpResponseBadRequest( template.render(context, request) )
    #     log.debug( 'returning bad-request response' )
    #     return bad_resp

    # end class Validator
