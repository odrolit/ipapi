from datetime import datetime
from connexion import NoContent, context
from connexion.resolver import MethodViewResolver
from flask import request, g, current_app
from flask.views import MethodView
from ipaddress import ip_address, ip_network, IPv4Address, IPv6Address, IPv4Network, IPv6Network 
from pymongo import MongoClient
from uuid import uuid4, UUID

from pprint import pprint



class log():
  '''
  logging class
  '''
  def d(*args, **kwargs):
    '''
    log debug
    '''
    app = current_app._get_current_object()
    app.logger.debug(*args, **kwargs)
    log.dd()

  def i(*args, **kwargs):
    '''
    log info
    '''
    app = current_app._get_current_object()
    app.logger.info(*args, **kwargs)
    log.dd()

  def w(*args, **kwargs):
    '''
    log warning
    '''
    app = current_app._get_current_object()
    app.logger.warning(*args, **kwargs)
    log.dd()

  def e(*args, **kwargs):
    '''
    log error
    '''
    app = current_app._get_current_object()
    app.logger.error(*args, **kwargs)
    log.dd()
  
  def dd():
    '''
    log delimitier
    '''
    app = current_app._get_current_object()
    app.logger.debug('-'*33)




class base:
  '''
  base class contains basic properties and functions extended by child classes
  '''
  
  def __init__(self, data, data_source = 'request'):
    '''
    puts data to self.data and sets object properties
    
    data_source can be request or db
    
    data_source request accepts dict as data
    
    data_source db accepst _id as data
    '''
    self.data = data
    self.data_source = data_source
    self._user_name = data['_user_name']
    self._user_ip = data['_user_ip']
    if self.data_source == 'request':
      self._provider_name = context['user']
      self._provider_ip = request.remote_addr
      self._class = self.__class__.__name__
      #data
      self.data['_id'] = uuid4()
      #meta
      self._set_meta()
    elif self.data_source == 'db':
      self._provider_name = self.data['_meta']['_provider_name']
      self._provider_ip = self.data['_meta']['_provider_name']
      self._class = self.__class__.__name__
      assert self._class == self.data['_meta']['_class']
      #data
      self.data = self._find_one({'_id': UUID(data)})
    elif self.data_source == 'database_initialization':
      self._provider_name = 'root'
      self._provider_ip = '127.0.0.1'
      self._class = self.__class__.__name__
      #data
      self.data['_id'] = uuid4()
      self.data['_meta'] = {}
      self.data['_meta']['_provider_name'] = self._provider_name
      self.data['_meta']['_provider_ip'] = self._provider_ip
      self.data['_meta']['_class'] = self._class
      self.data['_meta']['_valid'] = True
      self.data['_meta']['_valid_from'] = datetime.now()
      self.data['_meta']['_valid_to'] = datetime.max
    else:
      raise AttributeError('Unknown data_source')
    log.d(self.data)
  
  def _set_meta():
    '''
    set meta after request or before _save
    '''
    self.data['_meta'] = {}
    self.data['_meta']['_provider_name'] = self._provider_name
    self.data['_meta']['_provider_ip'] = self._provider_ip
    self.data['_meta']['_class'] = self._class
    self.data['_meta']['_valid'] = True
    self.data['_meta']['_valid_from'] = datetime.now()
    self.data['_meta']['_valid_to'] = datetime.max
    
  def connect_db(f):
    '''
    connect database to g.ipapi and
    all collections classes to g.colection_name
    TODO disconnection
    '''
    def wrapper(*args, **kwargs):
      if not 'db' in g:
        client = MongoClient('mongodb://127.0.0.1:27017')
        g.ipapi = client.ipapi
        log.d('Connected database ipapi to g.ipapi')
        for i in base.collections():
          # g[i] = g.ipapi[i] throws exception
          # TypeError: '_AppCtxGlobals' object does not support item assignment
          setattr(g, i, g.ipapi[i])
          log.d(f'Connected collection {i} to g.{i}')
      return f(*args, **kwargs)
    return wrapper
  
  def validate_provider_ip(f):
    '''
    checks if request.remote_addr is in allowed
    provider_ipv4 or provider_ipv6 network
    '''
    def wrapper(*args, **kwargs):
      ip = ip_address(request.remote_addr)
      if ip.version == 4:
        for i in context['token_info']['provider_ipv4']:
          if ip in IPv4Network(i):
            # ok
            return f(*args, **kwargs)
      elif ip.version == 6:
        for i in context['token_info']['provider_ipv6']:
          if ip in IPv6Network(i):
            # ok
            return f(*args, **kwargs)
      # ko
      return 'Provider IP not allowed', 401
    return wrapper
  
  def validate_user_ip(f):
    '''
    checks if data['_user_ip'] is in allowed
    user_ipv4 or user_ipv6 network
    TODO
    '''
    def wrapper(*args, **kwargs):
      return f(*args, **kwargs)
    return wrapper
  
  def validate_provider_access_get(f):
    '''
    TODO
    '''
    def wrapper(*args, **kwargs):
      return f(*args, **kwargs)
    return wrapper
  
  def validate_user_access_get(f):
    '''
    TODO
    '''
    def wrapper(*args, **kwargs):
      return f(*args, **kwargs)
    return wrapper
  
  def _get_parents(self):
    '''
    method must be defined by child class,
    returns list containing direct parents or root document
    '''
    raise NotImplementedError()
  
  def _set_parents(self):
    '''
    default is to set parents of the same class
    and do not touch other parents
    
    can be overidden in child class
    '''
    if 'parents' not in self.data:
      self.data['parents'] = {}
    self.data['parents'][self._class] = []
    for i in self._get_parents():
      self.data['parents'][self._class].append(i['_id'])
  
  def _set_meta(self):
    '''
    create or update document, takes care about _meta versions
    TODO
    '''
    # check if document exists
    
    # document does not exist and is created
    self.data['_meta']['_number'] = 1 #TODO
    self.data['_meta']['_uuid_valid'] = None
    # document exists and is updated
  
  def _save(self):
    '''
    saves document
    '''
    raise NotImplementedError()
  
  def _find_one(self, data):
    '''
    find one document
    '''
    raise NotImplementedError()
  
  def _load_if_exists(self, data):
    '''
    returns existing document or None
    TODO
    '''
    pass
  
  def json_one(data):
    '''
    print debug and returns data
    '''
    log.d(data)
    return data
  
  @staticmethod
  def json_multi(data):
    '''
    print debug and return list of objects
    '''
    a = []
    for i in data:
      a.append(i)
    log.d(a)
    return a
  
  @staticmethod
  def collections():
    """
    Get all collections names
    """
    return (i.__name__ for i in base.__subclasses__())
  
  @connect_db
  @validate_provider_ip
  @validate_user_ip
  @validate_provider_access_get
  @validate_user_access_get
  def post(self):
    '''
    create document
    TODO
    '''
    self._set_parents()
    #TODO _set_access, _set_meta wrappery
    #TODO change parents and childs
    self._save()
    return self.data, 201
    col = getattr(g, cls.__name__)
    i = getattr(ipapi, cls.__name__)
    print(i)
    a = self.__init__(data)
    col.insert_one(a.data)
    log.i(a.data)
    return a.data, 201
    # load parents
    
    # check if user has access
    col = getattr(g, cls.__name__)
    #new = 
    #TODO set parents
    data['_id'] = col.insert_one(data).inserted_id
    return base.json_one(data), 201
  
  @classmethod
  @connect_db
  @validate_provider_ip
  @validate_user_ip
  @validate_provider_access_get
  @validate_user_access_get
  def get(cls, _id = None):
    col = getattr(g, cls.__name__)
    if _id:
      a = col.find_one({'_id': UUID(_id)})
      if a:
        return base.json_one(a)
      return NoContent, 404
    else:
      return base.json_multi(col.find()), 200
  
  @connect_db
  @validate_provider_ip
  @validate_user_ip
  @validate_provider_access_get
  @validate_user_access_get
  def delete():
    if self.data and self.data['active']:
      self.data['active'] = False
      self._set_meta()
      self._save()
      log.i(self.data)
      return NoContent, 204
    return NoContent, 404



