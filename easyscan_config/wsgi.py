"""
WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os, pprint, sys
import shellvars


# print( 'the initial env, ```{}```'.format( pprint.pformat(dict(os.environ)) ) )

PROJECT_DIR_PATH = os.path.dirname( os.path.dirname(os.path.abspath(__file__)) )
ENV_SETTINGS_FILE = os.environ['EZSCAN__SETTINGS_PATH']  # set in `conf.d/passenger.conf`, and `env/bin/activate`

## update path
sys.path.append( PROJECT_DIR_PATH )

## Note: no need to activate the virtual-environment
## - the project's httpd/passenger.conf section allows specification of the python-path via `PassengerPython`, which auto-activates it
## - the auto-activation provides access to modules, but not, automatically, env-vars
## - env-vars loading under python3.x occurs via the `SenEnv` entry in the project's passenger.conf section
##   - requires apache env_module; info: <https://www.phusionpassenger.com/library/indepth/environment_variables.html>

## reference django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'iip_smr_config.settings'  # so django can access its settings

## load up env vars
var_dct = shellvars.get_vars( ENV_SETTINGS_FILE )
for ( key, val ) in var_dct.items():
    os.environ[key.decode('utf-8')] = val.decode('utf-8')

# print( 'the final env, ```{}```'.format( pprint.pformat(dict(os.environ)) ) )

## gogogo
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()






# """
# WSGI config for easyscan_project project.

# It exposes the WSGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
# """

# # import os
# # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "easyscan_config.settings")

# # from django.core.wsgi import get_wsgi_application
# # application = get_wsgi_application()



# """ Prepares application environment.
#     Variables assume project setup like:
#     easyscan_stuff
#         easyscan_project
#             easyscan_config
#             easyscan_app
#         env_ezscan
#      """

# import os, pprint, sys


# ## become self-aware, padawan
# current_directory = os.path.dirname(os.path.abspath(__file__))

# ## vars
# ACTIVATE_FILE = os.path.abspath( u'%s/../../env_ezscan/bin/activate_this.py' % current_directory )
# PROJECT_DIR = os.path.abspath( u'%s/../../easyscan_project' % current_directory )
# PROJECT_ENCLOSING_DIR = os.path.abspath( u'%s/../..' % current_directory )
# SETTINGS_MODULE = u'easyscan_config.settings'
# SITE_PACKAGES_DIR = os.path.abspath( u'%s/../../env_ezscan/lib/python2.6/site-packages' % current_directory )

# ## virtualenv
# execfile( ACTIVATE_FILE, dict(__file__=ACTIVATE_FILE) )

# ## sys.path additions
# for entry in [PROJECT_DIR, PROJECT_ENCLOSING_DIR, SITE_PACKAGES_DIR]:
#  if entry not in sys.path:
#    sys.path.append( entry )

# ## environment additions
# os.environ[u'DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULE  # so django can access its settings

# ## gogogo
# from django.core.wsgi import get_wsgi_application
# application = get_wsgi_application()
