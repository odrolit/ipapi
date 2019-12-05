###########################


LOGLEVEL = 'DEBUG'


###########################


import connexion
from connexion.resolver import MethodViewResolver
app = connexion.FlaskApp(__name__,
                         specification_dir='openapi/',
                         debug=True)


from .apikey import apikey_auth
from .base import base, log
from .ipv4 import ipv4, Ipv4View
from .router import RouterView



# load api
app.add_api('base.yaml',
            options={"swagger_ui": True},
            arguments={'title': 'MethodViewResolver ipapi'},
            resolver=MethodViewResolver('ipapi'), strict_validation=True, validate_responses=False)

app.app.logger.setLevel(LOGLEVEL)
app.app.logger.warning(f'Logging configured at level {LOGLEVEL}')



application = app.app
