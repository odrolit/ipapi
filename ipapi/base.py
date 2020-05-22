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
#TODO deepcopy delete ?
from re import match

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
    "title": "Bad request",
    "type": "about:blank"
    }, 400
  log.e(e)
  return e

def e401(detail):
  '''
  logs error and returns data in json
  '''
  e = {
    "detail": str(detail),
    "status": 401,
    "title": "Unauthorized",
    "type": "about:blank"
    }, 401
  log.e(e)
  return e

def e404(detail):
  '''
  logs error and returns data in json
  '''
  e = {
    "detail": str(detail),
    "status": 404,
    "title": "Not found",
    "type": "about:blank"
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
    "title": "Conflict",
    "type": "about:blank"
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
  
  True means same class parents are set implicitly,
  following funcions must be then defined:
  - _I_P_is_leaf()
  - _I_P_is_parent_of(parent)
  '''
  
  def __init__(self, data, data_source = 'request'):
    '''
    puts data to self.data and sets object properties
    
    data_source can be:
    - request (default)
    - db
    - copy
        
    request (default)
    - accept dict as data
    - _set_meta according to request
    
    db
    - accept _id as data
    - get data from db, _meta is unchanged
    
    copy
    - accept _id as data
    - get data from db, change _meta._valid,
      _meta._valid_to and _id and saves it
      as new document
    - _set_meta according to request,
      restore original _id, adjust _meta._valid_from,
      _meta._uuid_previous, _meta._version
      and return it for other modification
    '''
    self.data_source = data_source
    self._class = self.__class__.__name__
    log.d(('__init__', self._class, self.data_source, data))
    if self.data_source in ['request', 'database_initialization']:
      self.data = data
      self._set_meta()
    elif self.data_source in ['db', 'copy']:
      #usually we get _id as type str,
      #but we allow _id to be type UUID,
      #UUID(UUID(_id)) throws exception
      data = str(data)
      self.data = self._find_one({'_id': UUID(data)})
      if not self.data:
        raise AttributeError(f'Not found {self._class} {data}')
    else:
      raise AttributeError(f'Unknown data_source {data_source}')
    if self.data_source == 'copy':
      #save old copy
      self.data['_id'] = uuid4()
      self.data['_meta']['_valid'] = False
      self.data['_meta']['_valid_to'] = datetime.now()
      self._insert_one()
      #make new
      old_id = deepcopy(self.data['_id'])
      old_now = deepcopy(self.data['_meta']['_valid_to'])
      old_version = deepcopy(self.data['_meta']['_version'])
      self._set_meta()
      self.data['_id'] = UUID(data)
      self.data['_meta']['_valid_from'] = old_now
      self.data['_meta']['_uuid_previous'] = old_id
      self.data['_meta']['_version'] = old_version + 1
    log.d(('__init__', self._class, self.data_source, data))
  
  def _set_meta(self):
    '''
    set meta parameters to current request context
    
    used after request or before _insert_one
    '''
    self.data['_id'] = uuid4()
    self.data['_user_name'] = g._user_name
    self.data['_user_ip'] = g._user_ip
    self.data['_meta'] = {}
    self.data['_meta']['_provider_name'] = g._provider_name
    self.data['_meta']['_provider_ip'] = g._provider_ip
    self.data['_meta']['_class'] = self._class
    self.data['_meta']['_valid'] = True
    self.data['_meta']['_valid_from'] = datetime.now()
    self.data['_meta']['_valid_to'] = datetime.max
    #rest must me set individually
    self.data['_meta']['_version'] = None
    self.data['_meta']['_uuid_valid'] = None
    
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
      else:
        log.w('Database was already connected')
      return f(*args, **kwargs)
    return wrapper
  
  def validate_provider(f):
    '''
    checks if request.remote_addr is in allowed
    provider_ipv4 or provider_ipv6 network
    
    set g._provider_name and g._provider_ip
    '''
    def wrapper(*args, **kwargs):
      g._provider_name = context['user']
      g._provider_ip = request.remote_addr
      ip = ip_address(g._provider_ip)
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
      return e401('Provider IP not allowed')
    return wrapper
  
  def validate_user(f):
    '''
    checks if data['_user_name'] exists
    and is active
    
    checks if data['_user_ip'] is in allowed
    user_ipv4 or user_ipv6 network
    
    set g._user_name and g._user_ip
    '''
    def wrapper(*args, **kwargs):
      #TODO
      if request.method == 'POST':
        #POST
        g._user_name = args[1]['_user_name']
        g._user_ip = args[1]['_user_ip']
      else:
        #GET, PUT, DELETE
        g._user_name = kwargs['_user_name']
        g._user_ip = kwargs['_user_ip']
      return f(*args, **kwargs)
    return wrapper
  
  def validate_user_access_get(f):
    '''
    TODO
    '''
    def wrapper(*args, **kwargs):
      return f(*args, **kwargs)
    return wrapper
  
  def _C_C_get_parents(self):
    '''
    method must be defined by child class,
    returns list containing direct parents or root document
    '''
    log.e('_C_C_get_parents')
    raise NotImplementedError()
  
  @classmethod
  def _get_children(cls, _id):
    '''
    returns list containing all
    active and valid children
    '''
    log.d(('_get_children', _id))
    p = 'parents.' + cls.__name__
    r = []
    for i in cls._find_multi_simple({
      p: _id,
      'active': True,
      '_meta._valid': True}):
      if i:
        r.append(i)
    log.d(('_get_children', r))
    return r
  
  def _set_parents(self):
    '''
    IMPLICIT_PARENTS

    False means user defined same class parents
    are preserved or added if missing
  
    True means same class parents are set implicitly
    '''
    log.d(('_set_parents', self.data))
    if 'parents' not in self.data:
      self.data['parents'] = {}
    if self._class not in self.data['parents']:
      self.data['parents'][self._class] = []
    if self.IMPLICIT_PARENTS:
      #force clear submitted parents
      self.data['parents'][self._class] = []
      for i in self._C_C_get_parents():
        self.data['parents'][self._class].append(str(i['_id']))
    elif self.data['parents'][self._class] == []:
      #only set parents if missing
      for i in self._C_C_get_parents():
        self.data['parents'][self._class].append(str(i['_id']))
    log.d(('_set_parents', self.data))
  
  def _add_access(self, added):
    '''
    in added['access'] walks through
      ['delete', 'get', 'patch', 'post', 'put']
    and if is missing in self.data['access']
      then is added
    
    to be used from iside _set_access
    '''
    if 'delete' in added['access']:
      for i in added['access']['delete']:
        self.data['access']['delete'].append(i)
    if 'get' in added['access']:
      for i in added['access']['get']:
        self.data['access']['get'].append(i)
    if 'patch' in added['access']:
      for i in added['access']['patch']:
        present = False
        for j in self.data['access']['patch']:
          if i['match'] == j['match']:
            present = True
            for ii in i['patch']:
              if ii not in j['patch']:
                j['patch'].append(ii)
        if not present:
          self.data['access']['patch'].append(i)
    if 'post' in added['access']:
      for i in added['access']['post']:
        self.data['access']['post'].append(i)
    if 'put' in added['access']:
      for i in added['access']['put']:
        self.data['access']['put'].append(i)
      
  
  def _set_access(self):
    '''
    root access is added always first
    
    if some access was defined,
      then it is preserved,
      to allow redefine access,
      be careful to not accidentaly loose access
    else
      access from parents of the
      same class is added
    
    _set_access should be callef AFTER _set_parents
    '''
    log.d(('_set_access', self.data))
    missing = False
    if 'access' not in self.data or not self.data['access']:
      #access not present, create
      missing = True
      self.data['access'] = {}
    else:
      #acces present, check attributes
      for i in self.data['access']:
        if i not in ['delete', 'get', 'patch', 'post', 'put']:
          raise AttributeError(f'_set_access: unknown access {i}')
    #create all attributes if missing
    if 'delete' not in self.data['access']:
      self.data['access']['delete'] = []
    if 'get' not in self.data['access']:
      self.data['access']['get'] = []
    if 'patch' not in self.data['access']:
      self.data['access']['patch'] = []
    if 'post' not in self.data['access']:
      self.data['access']['post'] = []
    if 'put' not in self.data['access']:
      self.data['access']['put'] = []
    #get root access
    a = {}
    r = g.group.find_one(
        {'name': 'root_delete', '_meta._valid': True},
        projection={'_id': 1})
    a['delete'] = [str(r['_id'])]
    r = g.group.find_one(
        {'name': 'root_get', '_meta._valid': True},
        projection={'_id': 1})
    a['get'] = [str(r['_id'])]
    r = g.group.find_one(
        {'name': 'root_patch', '_meta._valid': True},
        projection={'_id': 1})
    a['patch'] = [{'match': '.', 'patch': [str(r['_id'])]}]
    r = g.group.find_one(
        {'name': 'root_post', '_meta._valid': True},
        projection={'_id': 1})
    a['post'] = [str(r['_id'])]
    r = g.group.find_one(
        {'name': 'root_put', '_meta._valid': True},
        projection={'_id': 1})
    a['put'] = [str(r['_id'])]
    #add root access
    self._add_access({'access': a})
    #
    if missing:
      #add access from parents of the same class
      for i in self.data['parents'][self._class]:
        r = self._find_one({'_id': i})
        self._add_access(r)
    log.d(('_set_access', self.data))
  
  def _insert_one(self):
    '''
    saves document and returns _id
    '''
    log.d(('_insert_one', self.data))
    col = getattr(g, self._class)
    r = col.insert_one(self.data).inserted_id
    if not r:
      raise Exception('_insert_one: Could not insert document')
    log.d(('_insert_one', r))
    return r
  
  def _replace_one(self):
    '''
    replace document identified by self.data['_id'],
    self.data is used to replace document
    '''
    log.d(('_replace_one', self.data))
    col = getattr(g, self._class)
    r = col.replace_one({'_id': self.data['_id']}, self.data)
    if r.modified_count != 1:
      log.e(('_replace_one', self.data))
      raise Exception('_replace_one: Could not update document')
    log.i(('_replace_one', self.data))
    return True
  
  def _update_one_set(self, data):
    '''
    update document identified by self.data['_id'],
    {'$set': data} is used to update document
    '''
    log.d(('_update_one_set', self.data, data))
    col = getattr(g, self._class)
    r = col.update_one({'_id': self.data['_id']}, {'$set': data})
    if r.modified_count != 1:
      log.e(('_update_one_set', self.data, data))
      raise Exception('_update_one_set: Could not update document')
    log.i(('_update_one_set', self.data, data))
    return True
  
  def _C_C_already_exists(self, data):
    '''
    method must be defined by child class,
    returns True if already exists
    '''
    log.e('_C_C_already_exists')
    raise NotImplementedError()
  
  @classmethod
  def _find_one(cls, find, projection = None):
    '''
    find and return one document
    '''
    log.d(('_find_one', cls.__name__, find, projection))
    col = getattr(g, cls.__name__)
    if projection:
      r = col.find_one(find, projection=projection)
    else:
      r = col.find_one(find)
    log.d(('_find_one', cls.__name__, r))
    return r
  
  @classmethod
  def _find_multi(cls, find, projection, sort, skip, limit):
    '''
    find and return list of documents
    '''
    col = getattr(g, cls.__name__)
    return col.find(find, projection=projection, sort=sort, skip=skip, limit=limit)
  
  @classmethod
  def _find_multi_simple(cls, find):
    '''
    find and return list of documents
    '''
    col = getattr(g, cls.__name__)
    return col.find(find)
  
  def json_one(self):
    '''
    print debug and returns self.data
    '''
    log.d(('json_one', self.data))
    self.data.pop('_bin', None)
    log.d(('json_one', self.data))
    return self.data
  
  @staticmethod
  def json_multi(data):
    '''
    print debug and return list of objects
    '''
    a = []
    if data:
      for i in data:
        a.append(i)
    log.d(('json_multi', a))
    return a
  
  @staticmethod
  def collections():
    """
    Get all collections names
    """
    return (i.__name__ for i in base.__subclasses__())
  
  @classmethod
  @connect_db
  @validate_provider
  @validate_user
  @validate_user_access_get
  def post(cls, data):
    '''
    create document if not exists
    
    TODO check for parental loops
    '''
    log.d(('post', data))
    a = cls(data)
    if a._C_C_already_exists():
      return e409('already exists')
    a._set_parents()
    a.data['_meta']['_version'] = 1
    a.data['_meta']['_uuid_valid'] = a.data['_id']
    a._set_access()
    a._insert_one()
    log.i(('post', a.data))
    if cls.IMPLICIT_PARENTS and not a._I_P_is_leaf():
      #check if parent's children are own children
      for i in a.data['parents'][a._class]:
        for ii in cls._get_children(i):
          if a._I_P_is_parent_of(ii):
            b = cls(ii['_id'], 'copy')
            #parents
            p = b.data['parents']
            #remove old parent
            p[a._class].remove(i)
            #add new parent
            p[a._class].append(str(a.data['_id']))
            #update
            b._replace_one()
    return a.json_one(), 201
  
  @classmethod
  @connect_db
  @validate_provider
  @validate_user
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
        log.d(('get', a))
        return a
      #404
      log.e(('get', _id, find, projection, sort, skip, limit, kwargs))
      return e404(f'get {_id}')
    else:
      a = cls._find_multi(find, projection=projection, sort=sort, skip=skip, limit=limit)
      #always return list, not 404
      return base.json_multi(a), 200
  
  @classmethod
  @connect_db
  @validate_provider
  @validate_user
  @validate_user_access_get
  def delete(cls, _id, **kwargs):
    '''
    delete document identified by _id
    by setting active = False
    '''
    log.d(('delete', _id, kwargs))
    old = cls._find_one({'_id': UUID(_id)})
    if not old:
      return e404(f'delete {_id} not found')
    if not old['_meta']['_valid']:
      return e409(f'delete {_id} not valid')
    if not old['active']:
      return e409(f'delete {_id} already deleted')
    if _id in old['parents'][cls.__name__]:
      return e409(f'delete {_id} root not allowed')
    if not cls.IMPLICIT_PARENTS:
      #active children are not allowed
      for i in cls._get_children(_id):
        if i['_meta']['_valid']:
          return e409(f'delete {_id} active child {i["_id"]}')
    a = cls(_id, 'copy')
    a.data['active'] = False
    #update
    a._replace_one()
    log.i(('delete', _id, a.data))
    if cls.IMPLICIT_PARENTS and not a._I_P_is_leaf():
      #move own children to parents
      for i in cls._get_children(_id):
        b = cls(i['_id'], 'copy')
        #parents
        p = b.data['parents']
        #remove old parent
        p[a._class].remove(_id)
        #add new parents
        for ii in a.data['parents'][a._class]:
          p[a._class].append(str(ii))
        #update
        b._replace_one()
    return NoContent, 204


