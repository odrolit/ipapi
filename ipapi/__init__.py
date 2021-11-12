###########################


#LOGLEVEL = 'DEBUG'
LOGLEVEL = 'WARNING'


###########################


import connexion
from connexion.resolver import MethodViewResolver
from flask import g
from datetime import datetime

from .apikey import apikey_auth
from .base import base, log
from .user import user, UserView
from .access import access, AccessView
from .ipv4 import ipv4, Ipv4View
from .ipv4nexthop import ipv4nexthop, Ipv4nexthopView


from .custom.nexthop import ipv4_nexthop_add, ipv4_nexthop_del



def create_app():
  '''
  application factory
  '''
  app = connexion.FlaskApp(__name__,
                          specification_dir='openapi/',
                          debug=False)
  
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
    if hasattr(g, 'rid'):
      rid = str(g.rid)
      del g.rid
      log.d((rid, str(datetime.now()), 'disconnect_db',
             f'removed request {rid}'))
    else:
      rid = None
    if hasattr(g, 'ipapi'):
      for i in base.collections():
        '''
        g[i] = g.ipapi[i] throws exception
        TypeError: '_AppCtxGlobals' object does not
        support item assignment
        '''
        g.pop(i, None)
        log.d((rid, str(datetime.now()), 'disconnect_db',
               f'disconnect collection {i}'))
      g.ipapi.client.close()
      del g.ipapi
      log.d((rid, str(datetime.now()), 'disconnect_db',
             'disconnect database ipapi'))
    #else:
      #log.e((rid, str(datetime.now()), 'disconnect_db',
             #'ipapi not connected (please ignore during database_initialization
             #and openapi/ui manipulation)'))
  
  return app

application = app = create_app()


