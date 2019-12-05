#common
DEBUG = True
SECRET_KEY = 'please change this secret key, this one is not secure'

#mongodb settings
MONGODB_SETTINGS = {
        'db': 'ipapi',
        'host': '127.0.0.1',
        'port': 27017}

#webserver settings
WEBSERVER_SETTINGS = {
  'ip': '0.0.0.0',
  'port': 5000}

#user settings
USER_APP_NAME = "ipapi"
USER_ENABLE_EMAIL = True
USER_ENABLE_USERNAME = False
USER_REQUIRE_RETYPE_PASSWORD = False
USER_EMAIL_SENDER_EMAIL = 'user@ip'
