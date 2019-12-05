###########################


LOGLEVEL = 'DEBUG'


###########################


import connexion
from connexion.resolver import MethodViewResolver
from flask import g

from .apikey import apikey_auth
from .base import base, log
from .ipv4 import ipv4, Ipv4View
from .router import RouterView



def create_app():
  '''
  application factory
  '''
  app = connexion.FlaskApp(__name__,
                          specification_dir='openapi/',
                          debug=True)
  # load api
  app.add_api('base.yaml',
              options={"swagger_ui": True},
              arguments={'title': 'MethodViewResolver ipapi'},
              resolver=MethodViewResolver('ipapi'),
              strict_validation=True,
              validate_responses=False)
  
  # set logging
  app.app.logger.setLevel(LOGLEVEL)
  with app.app.app_context():
    log.i(f'Logging configured at level {LOGLEVEL}')
  
  return app
