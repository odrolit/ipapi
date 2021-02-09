###########################


LOGLEVEL = 'DEBUG'
#LOGLEVEL = 'WARNING'


###########################


import connexion
from connexion.resolver import MethodViewResolver
from flask import g

from .apikey import apikey_auth
from .base import base, log
from .ipv4 import ipv4, Ipv4View
from .user import user, UserView
from .group import group, GroupView
from .router import RouterView

from .custom.blackhole import ipv4_blackhole_add, ipv4_blackhole_del



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

  @app.app.teardown_appcontext
  def disconnect_db(e):
    '''
    disconnects db at the end of request
    '''
    if hasattr(g, 'ipapi'):
      for i in base.collections():
        # g[i] = g.ipapi[i] throws exception
        # TypeError: '_AppCtxGlobals' object does not support item assignment
        g.pop(i, None)
        log.d(f'Disconnected collection {i}')
      g.ipapi.client.close()
      del g.ipapi
      log.d('Disconnected database ipapi')
  
  return app

application = app = create_app()


