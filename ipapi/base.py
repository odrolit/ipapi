from datetime import datetime
from connexion import NoContent, context
from connexion.resolver import MethodViewResolver
from flask import request, g, current_app
from flask.views import MethodView
from ipaddress import ip_address, ip_network, IPv4Address, IPv6Address, IPv4Network, IPv6Network 
from pymongo import MongoClient
from uuid import uuid4, UUID
from json import loads
from bson import json_util
from copy import deepcopy

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

def e400(detail):
  '''
  logs error and returns data in json
  '''
  e = {
    "detail": str(detail),
    "status": 400,
    "title": "Bad request"
    }, 400
  log.e(e)
  return e

def e404(detail):
  '''
  logs error and returns data in json
  '''
  e = {
    "detail": str(detail),
    "status": 404,
    "title": "Not found"
    }, 404
  log.e(e)
  return e

def e409(detail):
  '''
  logs error and returns data in json
  '''
  e = {
    "detail": str(detail),
    "status": 409,
    "title": "Conflict"
    }, 409
  log.e(e)
  return e

class base:
  '''
  basic properties and functions
  '''
  
  IMPLICIT_PARENTS = False
  '''
  IMPLICIT_PARENTS
  
  False means user defined same class parents
  are preserved or added if missing
  
  True means same class parents are set implicitly
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
      log.i('__init__')
      raise AttributeError('Unknown data_source')
    log.d(self.data)
  
  def _set_meta(self):
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
    
    disconnection is done by disconnect_db
    '''
    def wrapper(*args, **kwargs):
      if not 'ipapi' in g:
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
      log.i('validate_provider_ip')
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
    log.i('_get_parents')
    raise NotImplementedError()
  
  def _set_parents(self):
    '''
    IMPLICIT_PARENTS

    False means user defined same class parents
    are preserved or added if missing
  
    True means same class parents are set implicitly
    '''
    if 'parents' not in self.data:
      self.data['parents'] = {}
    if self._class not in self.data['parents']:
      self.data['parents'][self._class] = []
    if self.IMPLICIT_PARENTS:
      #force clear submitted parents
      self.data['parents'][self._class] = []
      for i in self._get_parents():
        self.data['parents'][self._class].append(i['_id'])
    elif self.data['parents'][self._class] == []:
      #only set parents if missing
      for i in self._get_parents():
        self.data['parents'][self._class].append(i['_id'])
  
  def _save(self):
    '''
    method must be defined by child class,
    saves document and returns _id
    '''
    log.i('_save')
    raise NotImplementedError()
  
  def _already_exists(self, data):
    '''
    method must be defined by child class,
    returns True if already exists
    '''
    log.i('_already_exists')
    raise NotImplementedError()
  
  @classmethod
  def _find_one(cls, find, projection = None):
    '''
    find and return one document
    '''
    col = getattr(g, cls.__name__)
    if projection:
      return col.find_one(find, projection=projection)
    return col.find_one(find)
  
  @classmethod
  def _find_multi(cls, find, projection, sort, skip, limit):
    '''
    find and return list of documents
    '''
    col = getattr(g, cls.__name__)
    return col.find(find, projection=projection, sort=sort, skip=skip, limit=limit)
  
  @staticmethod
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
    if data:
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
  @validate_user_access_get
  def post(self):
    '''
    create document
    
    check if already exists
    
    TODO
    '''
    if self._already_exists():
      return e409('Already exists')
    self._set_parents()
    #TODO _set_access
    #TODO change parents and childs
    _id = str(self._save())
    return self.get(_id), 201

  @classmethod
  @connect_db
  @validate_provider_ip
  @validate_user_ip
  @validate_user_access_get
  def get(cls, _id = None, find = None, projection = None, sort = None, skip = 0, limit = 0, **kwargs):
    '''
    if _id is specified, get document identified by _id,
    all other paramaters except projection are omitted,
    404 is returned if nothing found
    
    else get whole collection with other attributes applied,
    while only valid documents are returned by default,
    empty list is returned instead if nothing found
    
    Attributes description:
    https://docs.mongodb.com/manual/reference/operator/query/
    '''
    try:
      log.d(('get', _id, find, projection, sort, skip, limit, kwargs))
      if _id:
        _id = UUID(_id)
      if find:
        find = loads(find)
        assert type(find) is dict
      else:
        find = {'_meta._valid': True}
      if projection:
        projection = loads(projection)
        assert type(projection) is dict
        #binary hook
        projection.pop('_bin', None)
      else:
        #binary hook
        projection = {'_bin': 0}
      if sort:
        sort = loads(sort)
        assert type(sort) is dict
        sort = [(i, sort[i]) for i in sort]
      log.d(('get', _id, find, projection, sort, skip, limit, kwargs))
      if _id:
        a = cls._find_one({'_id': _id}, projection=projection)
        if a:
          return base.json_one(a)
        #404
        log.e(('get', _id, find, projection, sort, skip, limit, kwargs))
        return e404(f'get')
      else:
        a = cls._find_multi(find, projection=projection, sort=sort, skip=skip, limit=limit)
        #always return list, not 404
        return base.json_multi(a), 200
    except Exception as e:
      return e400(e)
  
  @classmethod
  @connect_db
  @validate_provider_ip
  @validate_user_ip
  @validate_user_access_get
  def delete(cls, _id, data):
    '''
    delete document by setting active = False
    
    TODO @validate_provider_access_delete
    '''
    print('test')
    data['_id'] = _id
    a = cls(data, 'db')
    print('test')
    if self.data and self.data['active']:
      self.data['active'] = False
      self._set_meta()
      self._save()
      log.i(self.data)
      return NoContent, 204
    log.i('delete')
    return NoContent, 404



