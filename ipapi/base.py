from datetime import datetime
from connexion import NoContent, context
from connexion.resolver import MethodViewResolver
from flask import request, g, current_app
from flask.views import MethodView
from ipaddress import ip_address, ip_network, IPv4Address, IPv6Address, IPv4Network, IPv6Network 
from pymongo import MongoClient, ASCENDING, DESCENDING
from uuid import uuid4, UUID
from json import loads
from bson import json_util
from re import match
from copy import deepcopy

from pprint import pprint

from time import sleep



def now():
  return str(datetime.now())



def rid():
  return str(g.rid)



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
    app.logger.debug('-'*30)

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

def e403(detail):
  '''
  logs error and returns data in json
  '''
  e = {
    "detail": str(detail),
    "status": 403,
    "title": "Access denied",
    "type": "about:blank"
    }, 403
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

  each user has access defined in list
    data['parents']['access']
  
  each item has access defined in lists
    data['access']['get']
    data['access']['post']
    data['access']['patch']
    data['access']['put']
    data['access']['delete']


  
  uniqueness is on name attribute by default,
  to change it the child class must define:
  - _C_U_get_active()
  - _C_U_get_active_valid_parents()
  


  child class can optionally define:
  - _C_O_parent_added()
  - _C_O_parent_deleted()
  - _C_O_child_added()
  - _C_O_child_deleted()



  IMPLICIT_PARENTS
  
  False means user defined same class parents
  are preserved or added if missing
  
  True means same class parents are set implicitly,
  following funcions must be then defined:
  - _I_P_is_leaf()
  - _I_P_is_parent_of(child)
  and uniqueness should be defined too:
  - _C_U_get_active()
  - _C_U_get_active_valid_parents()



  PRIVATE_PROPERTIES
  
  Contains propertis not allwed to patch
  using patch method, can be extended
  in child classes as needed
  '''
  
  IPAPI_VERSION = 1
  
  IMPLICIT_PARENTS = False
  
  PRIVATE_PROPERTIES = ['_id', '_meta', '_bin']
  
  def __init__(self, data, data_source = 'request'):
    '''
    puts data to self.data and sets object properties
    
    data_source can be:
    - request (default)
    - db
    - copy
    - copy_trust
    - database_initialization (only for db initialization)
        
    request (default)
    - accept dict as data
    - _set_meta according to request
    
    db
    - accept _id as data
    - get data from db, _meta is unchanged
    
    copy
    - accept _id as data
    - get data from db, change _meta._active,
      _meta._active_to and _id and saves it
      as new document
    - _set_meta according to request,
      restore original _id, adjust _meta._active_from,
      _meta._uuid_previous, _meta._version
      and return it for other modification
    
    copy_trust
    - same as copy, the data instead of _id
      are passed and not retrieved from db
    - we trust that data are correct
      and only active object are processed
    '''
    self.data_source = data_source
    self._class = self.__class__.__name__
    log.d((rid(), now(), '__init__', self._class, self.data_source, data))
    if self.data_source in ['request', 'database_initialization']:
      self.data = deepcopy(data)
      self._set_meta()
    elif self.data_source in ['db', 'copy']:
      #usually we get _id as type str,
      #but we allow _id to be type UUID,
      #UUID(UUID(_id)) throws exception
      data = str(data)
      self.data = self._find_one({'_id': UUID(data)})
    elif self.data_source == 'copy_trust':
      self.data = deepcopy(data)
    else:
      log.e((rid(), now(), '__init__', self._class, self.data_source, data))
      raise AttributeError(f'Unknown data_source {data_source}')
    if not self.data:
      log.e((rid(), now(), '__init__', self._class, self.data_source, data))
      raise AttributeError(f'Data not found, source {data_source}')
    if self.data_source in ['copy', 'copy_trust']:
      if not self.data['_meta']['_active']:
        log.e((rid(), now(), '__init__', self._class, self.data_source, data))
        raise AttributeError(f'Can not copy inactive {data["_id"]}')
      _id = self.data['_id']
      _now = datetime.now()
      _version = self.data['_meta']['_version']
      #save old copy
      self.data['_id'] = uuid4()
      self.data['_meta']['_active'] = False
      self.data['_meta']['_active_to'] = _now
      self._insert_one()
      #make new, _set_meta analogy
      self.data['_meta'] = {}
      self.data['_meta']['_uuid_previous'] = self.data['_id']
      #_uuid_previous must be set prior to _id changes back
      self.data['_id'] = _id
      self.data['_user_name'] = g._user_name
      self.data['_user_ip'] = g._user_ip
      self.data['_meta']['_provider_name'] = g._provider_name
      self.data['_meta']['_provider_ip'] = g._provider_ip
      self.data['_meta']['_ipapi_version'] = base.IPAPI_VERSION
      self.data['_meta']['_uuid_request'] = g.rid
      self.data['_meta']['_class'] = self._class
      self.data['_meta']['_valid'] = True
      self.data['_meta']['_active'] = True
      self.data['_meta']['_active_from'] = _now
      self.data['_meta']['_active_to'] = datetime.max
      self.data['_meta']['_uuid_active'] = _id
      self.data['_meta']['_version'] = _version + 1
    log.d((rid(), now(), '__init__', self._class, self.data_source, data))
  
  def _set_meta(self):
    '''
    set meta parameters to current request context
    
    used after request or before _insert_one
    '''
    log.d((rid(), now(), '_set_meta', self._class, self.data))
    self.data['_id'] = uuid4()
    self.data['_user_name'] = g._user_name
    self.data['_user_ip'] = g._user_ip
    self.data['_meta'] = {}
    self.data['_meta']['_provider_name'] = g._provider_name
    self.data['_meta']['_provider_ip'] = g._provider_ip
    self.data['_meta']['_ipapi_version'] = base.IPAPI_VERSION
    self.data['_meta']['_uuid_request'] = g.rid
    self.data['_meta']['_class'] = self._class
    self.data['_meta']['_valid'] = True
    self.data['_meta']['_active'] = True
    self.data['_meta']['_active_from'] = datetime.now()
    self.data['_meta']['_active_to'] = datetime.max
    #rest must me set individually
    self.data['_meta']['_uuid_previous'] = None
    self.data['_meta']['_uuid_active'] = None
    self.data['_meta']['_version'] = None
    log.d((rid(), now(), '_set_meta', self._class, self.data))
    
  def connect_db(f):
    '''
    connect database to g.ipapi and
    all collections classes to g.colection_name
    
    disconnection is done by disconnect_db
    '''
    def wrapper(*args, **kwargs):
      if 'rid' in g:
        log.w((rid(), now(), 'connect_db', 'Request ID already set'))
      else:
        g.rid = uuid4()
        log.d((rid(), now(), 'connect_db'))
      if 'ipapi' in g:
        log.w((rid(), now(), 'connect_db', 'Database ipapi already connected'))
      else:
        client = MongoClient('mongodb://127.0.0.1:27017')
        g.ipapi = client.ipapi
        log.d((rid(), now(), 'connect_db', 'connected database ipapi'))
        for i in base.collections():
          # g[i] = g.ipapi[i] throws exception
          # TypeError: '_AppCtxGlobals' object does not support item assignment
          setattr(g, i, g.ipapi[i])
          log.d((rid(), now(), 'connect_db', f'connected collection {i}'))
      return f(*args, **kwargs)
    return wrapper
  
  def validate_provider(f):
    '''
    checks if request.remote_addr is in allowed
    provider_ipv4 or provider_ipv6 network
    
    set g._provider_name and g._provider_ip
    '''
    #log.d((rid(), now(), 'validate_provider'))
    def wrapper(*args, **kwargs):
      g._provider_name = context['user']
      g._provider_ip = request.remote_addr
      ip = ip_address(g._provider_ip)
      #log.d((rid(), now(), 'validate_provider', g._provider_name, g._provider_ip, ip))
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
    #log.d((rid(), now(), 'validate_user'))
    def wrapper(*args, **kwargs):
      if request.method in ['POST', 'PATCH', 'PUT', 'DELETE']:
        g._user_name = args[1]['_user_name']
        g._user_ip = args[1]['_user_ip']
      else:
        #GET
        g._user_name = kwargs['_user_name']
        g._user_ip = kwargs['_user_ip']
      u = base.get_class('user')._find_one(
        {'_meta._active': True, 'name': g._user_name})
      if u and 'parents' in u and 'access' in u['parents']:
        g._user_access = u['parents']['access']
        assert type(g._user_access) is list
      else:
        log.e((rid(), now(), 'get', f'User {g._user_name} has no access'))
        return e403(f'User {g._user_name} has no access')
      #log.d((rid(), now(), 'validate_user', g._user_name, g._user_ip, g._user_access))
      return f(*args, **kwargs)
    return wrapper
  
  @classmethod
  def _user_has_access(cls, method, data, patch = None):
    '''
    methods can be get, post, put, patch and delete
    
    if method is patch, the patch parameter is required
    
    compare if there is intersection in
    g._user_access['method'] and data['access']['method']
    and returns bool
    '''
    #TODO remove hack
    log.d((rid(), now(), '_user_has_access', cls.__name__, method, data, patch))
    #return True
    if method in ['get', 'post', 'put', 'delete']:
      return any(i in data['access'][method]
                 for i in g._user_access)
    elif method == 'patch' and patch:
      for i in patch:
        #walk through all items in patch
        for j in data['access']['patch']:
          #walk through all data access patch rules
          if match(j['match'], i):
            #this data access patch rule match to item
            if any(k in j['patch']
                   for k in g._user_access):
              #success, access for this item is granted
              break
        else:
          #no access for this item
          log.w((rid(), now(), '_user_has_access', f'access denied {i}'))
          return False
      log.d((rid(), now(), '_user_has_access', 'access granted'))
      return True
    else:
      log.e((rid(), now(), '_user_has_access', f'unknown method {method}'))
      raise Exception(f'_user_has_access unknown method {method}')
  
  def _C_U_get_active(self):
    '''
    returns active document or None,
    the document can be valid or deleted
    '''
    log.d((rid(), now(), '_C_U_get_active'))
    r = self._find_one({'_meta._active': True,
                        'name': self.data['name']})
    log.d((rid(), now(), '_C_U_get_active', r))
    return r
  
  def _C_U_get_active_valid_parents(self):
    '''
    returns list containing direct active
    and valid parents or root document
    '''
    log.d((rid(), now(), '_C_U_get_active_valid_parents'))
    r = self._find_multi_simple({'_meta._active': True,
                                 '_meta._valid': True,
                                 'name': 'root'})
    log.d((rid(), now(), '_C_U_get_active_valid_parents', r.count()))
    return r
  
  @classmethod
  def _get_children_same_class(cls, _id):
    '''
    returns list containing all
    active and valid children
    in the same class
    '''
    log.d((rid(), now(), '_get_children_same_class', cls.__name__, _id))
    p = 'parents.' + cls.__name__
    r = []
    for i in cls._find_multi_simple({
      p: _id,
      '_meta._valid': True,
      '_meta._active': True}):
      if i:
        r.append(i)
    log.d((rid(), now(), '_get_children_same_class', cls.__name__, r))
    return r
  
  @classmethod
  def _get_children_all_classes(cls, _id):
    '''
    returns (bool, list)
    
    bool is true if at least one active
    child exists
    
    list contains all
    active and valid children
    in all classes
    '''
    log.d((rid(), now(), '_get_children_all_classes', cls.__name__, _id))
    p = 'parents.' + cls.__name__
    q = {'_meta._valid': True,
         '_meta._active': True,
         p: _id}
    b = False
    r = {}
    for i in base.collections():
      r[i] = []
      for j in base._find_multi_simple_other_class(i, q):
        if j:
          b = True
          r[i].append(str(j))
    log.d((rid(), now(), '_get_children_all_classes', cls.__name__, b, r))
    return b, r
  
  def _set_parents(self):
    '''
    
    IMPLICIT_PARENTS
    
    False means user defined same class parents
    are preserved or added if missing
    
    True means same class parents are set implicitly
    '''
    log.d((rid(), now(), '_set_parents', self.data))
    if 'parents' not in self.data:
      self.data['parents'] = {}
    if self._class not in self.data['parents']:
      self.data['parents'][self._class] = []
    if self.IMPLICIT_PARENTS:
      #force clear submitted parents
      self.data['parents'][self._class] = []
      for i in self._C_U_get_active_valid_parents():
        self.data['parents'][self._class].append(i['_id'])
    elif self.data['parents'][self._class] == []:
      #only set parents if missing
      for i in self._C_U_get_active_valid_parents():
        self.data['parents'][self._class].append(i['_id'])
    log.d((rid(), now(), '_set_parents', self.data))
  
  def _add_access(self, added):
    '''
    in added['access'] walks through
      ['delete', 'get', 'patch', 'post', 'put']
    and if is missing in self.data['access']
      then is added
    
    to be used from INSIDE _set_access
    '''
    log.d((rid(), now(), '_add_access', self.data, added))
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
    log.d((rid(), now(), '_add_access', self.data, added))
      
  
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
    log.d((rid(), now(), '_set_access', self.data))
    missing = False
    if 'access' not in self.data or not self.data['access']:
      #access not present, create
      missing = True
      self.data['access'] = {}
    else:
      #acces present, check attributes
      for i in self.data['access']:
        if i not in ('delete', 'get', 'patch', 'post', 'put'):
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
    r = base._find_one_other_class(
      'access',
      {'_meta._active': True, 'name': 'root'},
      projection={'_id': 1})
    if not r:
      log.e((rid(), now(), '_set_access', self.data,
             'database corrupted, missing root access'))
      raise Exception('_set_access: database corrupted, missing root access')
    #add root access
    self._add_access({'access': {
      'delete': [r['_id']],
      'get': [r['_id']],
      'patch': [{'match': '.', 'patch': [r['_id']]}],
      'post': [r['_id']],
      'put': [r['_id']]}})
    #
    if missing:
      #add access from parents of the same class
      for i in self.data['parents'][self._class]:
        r = self._find_one({'_id': i})
        self._add_access(r)
    log.d((rid(), now(), '_set_access', self.data))
  
  def _insert_one(self):
    '''
    saves document and returns _id
    '''
    log.d((rid(), now(), '_insert_one', self.data))
    col = getattr(g, self._class)
    r = col.insert_one(self.data, session=g.sess).inserted_id
    if not r:
      raise Exception('_insert_one: Could not insert document')
    log.i((rid(), now(), '_insert_one', r))
    return r
  
  def _replace_one(self):
    '''
    replace document identified by self.data['_id'],
    self.data is used to replace document
    '''
    log.d((rid(), now(), '_replace_one', self.data))
    col = getattr(g, self._class)
    r = col.replace_one({'_id': self.data['_id']}, self.data, session=g.sess)
    if r.modified_count != 1:
      log.e((rid(), now(), '_replace_one', r.raw_result))
      raise Exception('_replace_one: Could not update document')
    log.i((rid(), now(), '_replace_one', r.modified_count))
    return r
  
  def _update_one_set(self, data):
    '''
    update document identified by self.data['_id'],
    {'$set': data} is used to update document
    '''
    log.d((rid(), now(), '_update_one_set', self.data, data))
    col = getattr(g, self._class)
    r = col.update_one({'_id': self.data['_id']}, {'$set': data}, session=g.sess)
    if r.modified_count != 1:
      log.e((rid(), now(), '_update_one_set', self.data, data))
      raise Exception('_update_one_set: Could not update document')
    log.i((rid(), now(), '_update_one_set', r.modified_count))
    return True
  
  @classmethod
  def _find_one(cls, find, projection = None):
    '''
    find and return one document
    '''
    log.d((rid(), now(), '_find_one', cls.__name__, find, projection))
    col = getattr(g, cls.__name__)
    if projection:
      r = col.find_one(find, projection=projection)
    else:
      r = col.find_one(find)
    log.d((rid(), now(), '_find_one', cls.__name__, r))
    return r
  
  @staticmethod
  def _find_one_other_class(cls, find, projection = None):
    '''
    find and return one document
    '''
    log.d((rid(), now(), '_find_one_other_class', cls, find, projection))
    col = getattr(g, cls)
    if projection:
      r = col.find_one(find, projection=projection)
    else:
      r = col.find_one(find)
    log.d((rid(), now(), '_find_one_other_class', cls, r))
    return r
  
  @classmethod
  def _find_multi(cls, find, projection, sort, skip, limit):
    '''
    find and return list of documents
    '''
    log.d((rid(), now(), '_find_multi', cls.__name__, find, projection, sort, skip, limit))
    col = getattr(g, cls.__name__)
    r = col.find(find, projection=projection, sort=sort, skip=skip, limit=limit)
    log.d((rid(), now(), '_find_multi', cls.__name__, r.count()))
    return r
  
  
  @classmethod
  def _find_multi_simple(cls, find, hint = None):
    '''
    find and return list of documents of this class
    '''
    log.d((rid(), now(), '_find_multi_simple', cls.__name__, find, hint))
    col = getattr(g, cls.__name__)
    if hint:
      r = col.find(find).hint(hint)
    else:
      r = col.find(find)
    log.d((rid(), now(), '_find_multi_simple', r.count()))
    return r
  
  @staticmethod
  def _find_multi_simple_other_class(cls, find):
    '''
    accepts class as string and find as dict,
    find and return list of documents of defined class
    '''
    log.d((rid(), now(), '_find_multi_simple_other_class', cls, find))
    col = getattr(g, cls)
    r = col.find(find)
    log.d((rid(), now(), '_find_multi_simple_other_class', cls, r.count()))
    return r

  def _document_become_valid(self, cls):
    '''
    should be used after each operation
    when document become valid
    
    if IMPLICIT_PARENTS, then check
      if parent's children are own children,
        then adopt them
    '''
    log.d((rid(), now(), '_document_become_valid', cls.__name__, self.data))
    if cls.IMPLICIT_PARENTS and not self._I_P_is_leaf():
      #check if parent's children are own children
      for i in self.data['parents'][self._class]:
        for ii in cls._get_children_same_class(i):
          if self._I_P_is_parent_of(ii):
            b = cls(ii['_id'], 'copy')
            #parents
            p = b.data['parents']
            #remove old parent
            p[self._class].remove(i)
            #add new parent
            p[self._class].append(str(self.data['_id']))
            #update
            b._replace_one()
    log.d((rid(), now(), '_document_become_valid', cls.__name__, self.data))
  
  def _check_document_parents(self, old):
    '''
    should be used after each operation
    when document changed
    
    old is passed as data only (e.g. from db)
    
    walks through added parents and
      calls custom _C_O_parent_added function
    walks through deleted parents and
      calls custom _C_O_parent_deleted function
    
    raises exception if parental loop exists
    '''
    log.d((rid(), now(), '_check_document_parents', self.data, old))
    #check added parents
    for i in self.data['parents']:
      if i in old['parents']:
        for j in self.data['parents'][i]:
          if j not in old['parents'][i]:
            #instantiate parent from db
            p = base.get_class(i)(j, 'db')
            self._C_O_parent_added(p)
            p._C_O_child_added(self)
      else:
        for j in self.data['parents'][i]:
          #instantiate parent from db
          p = base.get_class(i)(j, 'db')
          self._C_O_parent_added(p)
          p._C_O_child_added(self)
    #check deleted parents
    for i in old['parents']:
      if i in self.data['parents']:
        for j in old['parents'][i]:
          if j not in self.data['parents'][i]:
            #instantiate parent from db
            p = base.get_class(i)(j, 'db')
            self._C_O_parent_deleted(p)
            p._C_O_child_deleted(self)
      else:
        for j in old['parents'][i]:
          #instantiate parent from db
          p = base.get_class(i)(j, 'db')
          self._C_O_parent_deleted(p)
          p._C_O_child_deleted(self)
    if base._parental_loop_exists(self.data['_id'], self.data):
      #documents with walid children can not be deleted
      log.e((rid(), now(), '_check_document_parents', self.data, old))
      raise Exception('_parental_loop_exists')
    log.d((rid(), now(), '_check_document_parents', self.data, old))
  
  @staticmethod
  def _parental_loop_exists(_id, data):
    '''
    walks through all parents, including foreign
    classes and returns True if a loop exists
    '''
    log.d((rid(), now(), '_parental_loop_exists', _id, data))
    for i in data['parents']:
      if _id in data['parents'][i]:
        return True
      #col = getattr(g, i)
      cls = base.get_class(i)
      for j in data['parents'][i]:
        #classmethod _find_one is cleaner
        #jj = col.find_one({'_id': j}, {'parents': 1})
        jj = cls._find_one({'_id': j}, {'parents': 1})
        if jj and base._parental_loop_exists(_id, jj):
          return True
  
  def _C_O_parent_added(self, parent):
    '''
    custom handling when parent was added
    
    expects parent instance as parameter
    '''
    log.d((rid(), now(), '_C_O_parent_added', self._class, self.data['_id'],
           parent._class, parent.data['_id']))
  
  def _C_O_parent_deleted(self, parent):
    '''
    custom handling when parent was deleted
        
    expects parent instance as parameter
    '''
    log.d((rid(), now(), '_C_O_parent_deleted', self._class, self.data['_id'],
           parent._class, parent.data['_id']))
  
  def _C_O_child_added(self, child):
    '''
    custom handling when child was added
    
    expects child instance as parameter
    '''
    log.d((rid(), now(), '_C_O_child_added', self._class, self.data['_id'],
           child._class, child.data['_id']))
  
  def _C_O_child_deleted(self, child):
    '''
    custom handling when child was deleted
        
    expects child instance as parameter
    '''
    log.d((rid(), now(), '_C_O_child_deleted', self._class, self.data['_id'],
           child._class, child.data['_id']))
  
  def _document_become_invalid(self, cls):
    '''
    should be used after each operation
    when document become invalid
    
    if IMPLICIT_PARENTS and self is not leaf,
      then get them adopted by parent
    '''
    log.d((rid(), now(), '_document_become_invalid', cls.__name__, self.data))
    if cls.IMPLICIT_PARENTS and not self._I_P_is_leaf():
      for i in cls._get_children_same_class(self.data['_id']):
        b = cls(i['_id'], 'copy')
        #parents
        p = b.data['parents']
        #remove old parent
        p[self._class].remove(self.data['_id'])
        #add new parents
        for ii in self.data['parents'][self._class]:
          p[self._class].append(str(ii))
        #update
        b._replace_one()
    log.d((rid(), now(), '_document_become_invalid', cls.__name__, self.data))
  
  def json_one(self):
    '''
    print debug and returns self.data
    '''
    log.d((rid(), now(), 'json_one', self.data))
    self.data.pop('_bin', None)
    log.d((rid(), now(), 'json_one', self.data))
    return self.data
  
  @staticmethod
  def json_multi_user_has_access_get(cls, data, projection_access_hook = False):
    '''
    print debug and return list of objects
    '''
    log.d((rid(), now(), 'json_multi_user_has_access_get', cls.__name__, data.count(), projection_access_hook))
    r = []
    if data:
      for i in data:
        if i and cls._user_has_access('get', i):
          if projection_access_hook:
            i.pop('access')
          r.append(i)
        else:
          log.d((rid(), now(), 'json_multi_user_has_access_get', 'removed', i))
    log.d((rid(), now(), 'json_multi_user_has_access_get', r))
    return r
  
  @staticmethod
  def collections():
    """
    get all collections names
    """
    return (i.__name__ for i in base.__subclasses__())
  
  @staticmethod
  def get_class(name):
    """
    returns class by class name
    """
    for i in base.__subclasses__():
      if i.__name__ == name:
        return i
    log.e((rid(), now(), 'get_class', f'unknown class {name}'))
    raise Exception(f'get_class, unknown class {name}')
  
  @classmethod
  @connect_db
  @validate_provider
  @validate_user
  def get(cls, _id = None, find = None, projection = None, sort = None, skip = 0, limit = 0, **kwargs):
    '''
    if _id is specified, get document identified by _id,
    all other paramaters except projection are omitted,
    in this case returns:
      200 if document found
      400 bad request raised by enveloping view
      403 access denied
      404 if not found
      500 internal server error
    
    else get whole collection with other attributes applied,
      if _meta._active is not present in find,
        then _meta._active: True is added,
      if _meta._valid is not present in find,
        then _meta._valid: True is added,
    then it returns:
      200 and list of documents, empty list
        is returned if nothing found or
        if access denied to all documents
      400 bad request raised by enveloping view
      500 internal server error
    
    Attributes description:
    https://docs.mongodb.com/manual/reference/operator/query/
    '''
    log.d((rid(), now(), 'get', _id, find, projection, sort, skip, limit, kwargs))
    if _id:
      _id = UUID(_id)
    if find:
      find = loads(find)
      assert type(find) is dict
    else:
      find = {}
    if '_meta._active' not in find:
      find['_meta._active'] = True
    if '_meta._valid' not in find:
      find['_meta._valid'] = True
    projection_access_hook = False
    if projection:
      projection = loads(projection)
      assert type(projection) is dict
      #binary hook
      projection.pop('_bin', None)
      '''
      access hook is needed to get access from database,
      check the user access and remove it from returned data
      '''
      if 'access' not in projection or projection['access'] == 0:
        #TODO add more advanced projection options (access.get)
        projection['access'] = 1
        projection_access_hook = True
    else:
      #binary hook
      projection = {'_bin': 0}
    if sort:
      sort = loads(sort)
      assert type(sort) is dict
      sort = [(i, sort[i]) for i in sort]
    log.d((rid(), now(), 'get', _id, find, projection, sort, skip, limit, kwargs))
    if _id:
      a = cls._find_one({'_id': _id}, projection=projection)
      if a:
        if not cls._user_has_access('get', a):
          return e403('Access denied for method get')
        log.d((rid(), now(), 'get', a))
        return a
      #404
      log.e((rid(), now(), 'get', _id, find, projection, sort, skip, limit, kwargs))
      return e404('Not found {_id}')
    else:
      a = cls._find_multi(find, projection=projection, sort=sort, skip=skip, limit=limit)
      #always return list, not 404
      r = base.json_multi_user_has_access_get(cls, a, projection_access_hook)
      return r, 200
  
  @classmethod
  @connect_db
  @validate_provider
  @validate_user
  def post(cls, data):
    '''
    create document if not exists or is deleted, returns:
      201 document created
      400 bad request raised by enveloping view
      403 access denied
      409 document already exists
      500 internal server error
    '''
    log.d((rid(), now(), 'post', data))
    with g.ipapi.client.start_session() as s:
      if 'sess' in g:
        log.w(f'Session was already registered in g.sess')
      else:
        g.sess = s
        log.d(f'Session was registered to g.sess')
      with s.start_transaction():
        a = cls(data)
        old = a._C_U_get_active()
        if old and old['_meta']['_valid']:
          #document already exists
          return e409(f'already exists {old["_id"]}')
        elif old:
          #old document was deleted
          if not cls._user_has_access('post', old):
            return e403('Access denied for method post')
          b = cls(old, 'copy_trust')
          #delete old items
          for i in data:
            if i not in cls.PRIVATE_PROPERTIES:
              b.data.pop(i, None)
          # PRIVATE_PROPERTIES are guarded by openapi readOnly
          b.data.update(data)
          b._set_parents()
          for i in b.data['parents'][b._class]:
            #match access with class parents
            p = cls(i, 'db')
            if not cls._user_has_access('post', p.data):
              return e403('Access denied for method post')
          b._set_access()
          b._replace_one()
          b._check_document_parents(old)
          b._document_become_valid(cls)
          return b.json_one(), 201
        else:
          #create
          a.data['_meta']['_version'] = 1
          a.data['_meta']['_uuid_active'] = a.data['_id']
          a._set_parents()
          for i in a.data['parents'][a._class]:
            #match access with class parents
            p = cls(i, 'db')
            if not cls._user_has_access('post', p.data):
              return e403('Access denied for method post')
          a._set_access()
          a._insert_one()
          a._check_document_parents({'parents': {}})
          a._document_become_valid(cls)
          return a.json_one(), 201
  
  @classmethod
  @connect_db
  @validate_provider
  @validate_user
  def patch(cls, data):
    '''
    patch document or create if not exists, returns:
      200 document patched
      201 document created
      400 bad request raised by enveloping view
      403 access denied
      500 internal server error
    '''
    log.d((rid(), now(), 'patch', data))
    with g.ipapi.client.start_session() as s:
      if 'sess' in g:
        log.w(f'Session was already registered in g.sess')
      else:
        g.sess = s
        log.d(f'Session was registered to g.sess')
      with s.start_transaction():
        a = cls(data)
        old = a._C_U_get_active()
        #python 3.8: if old := a._C_U_get_active()
        if old:
          '''
          patch
          
          can't use "a", it already contains default values
          which could overwrite non-default in old document
          
          can't use "old", it is not class instance
          and there is no copy of it
          '''
          if not cls._user_has_access('patch', old, data):
            return e403('Access denied for method patch')
          b = cls(old, 'copy_trust')
          # PRIVATE_PROPERTIES are guarded by openapi readOnly
          b.data.update(data)
          b._set_parents()
          b._set_access()
          b._replace_one()
          b._check_document_parents(old)
          if not old['_meta']['_valid']:
            #old document was deleted
            b._document_become_valid(cls)
          return b.json_one(), 200
        else:
          #create
          a.data['_meta']['_version'] = 1
          a.data['_meta']['_uuid_active'] = a.data['_id']
          a._set_parents()
          for i in a.data['parents'][a._class]:
            #match access with class parents
            p = cls(i, 'db')
            if not cls._user_has_access('patch', p.data, data):
              return e403('Access denied for method patch')
          a._set_access()
          a._insert_one()
          a._check_document_parents({'parents': {}})
          a._document_become_valid(cls)
          return a.json_one(), 201
  
  @classmethod
  @connect_db
  @validate_provider
  @validate_user
  def delete(cls, data):
    '''
    delete document by setting _meta._valid = False, returns:
      204 deleted
      400 bad request raised by enveloping view
      403 access denied
      404 not found
      409 not alled to delete root document
      500 internal server error
    '''
    log.d((rid(), now(), 'delete', data))
    with g.ipapi.client.start_session() as s:
      if 'sess' in g:
        log.w(f'Session was already registered in g.sess')
      else:
        g.sess = s
        log.d(f'Session was registered to g.sess')
      with s.start_transaction():
        a = cls(data)
        old = a._C_U_get_active()
        if old and old['_meta']['_valid']:
          #document exists and is not deleted
          if not cls._user_has_access('delete', old):
            return e403('Access denied for method delete')
          if old['_id'] in old['parents'][cls.__name__]:
            return e409(f'delete {old["_id"]}, root document')
          b, r = cls._get_children_all_classes(old['_id'])
          if b:
            return e409(f'delete {old["_id"]}, valid children {r}')
          b = cls(old, 'copy_trust')
          b.data['_meta']['_valid'] = False
          b._replace_one()
          b._check_document_parents(old)
          b._document_become_invalid(cls)
          return NoContent, 204
        else:
          #document not exists or deleted
          if 'name' in data:
            return e404(f'Not found {data["name"]}')
          return e404('Not found')
  
  @classmethod
  @connect_db
  @validate_provider
  @validate_user
  def put(cls, data):
    '''
    replace document or create document if not exists, returns:
      200 document replaced
      201 document created
      400 bad request raised by enveloping view
      403 access denied
      500 internal server error
    '''
    log.d((rid(), now(), 'put', data))
    with g.ipapi.client.start_session() as s:
      if 'sess' in g:
        log.w(f'Session was already registered in g.sess')
      else:
        g.sess = s
        log.d(f'Session was registered to g.sess')
      with s.start_transaction():
        a = cls(data)
        old = a._C_U_get_active()
        #python 3.8: if old := a._C_U_get_active()
        if old:
          if not cls._user_has_access('put', old):
            return e403('Access denied for method put')
          b = cls(old, 'copy_trust')
          #delete old items
          for i in data:
            if i not in cls.PRIVATE_PROPERTIES:
              b.data.pop(i, None)
          # PRIVATE_PROPERTIES are guarded by openapi readOnly
          b.data.update(data)
          b._set_parents()
          b._set_access()
          b._replace_one()
          b._check_document_parents(old)
          if not old['_meta']['_valid']:
            #old document was deleted
            self._document_become_valid(cls)
          return b.json_one(), 200
        else:
          #create
          a.data['_meta']['_version'] = 1
          a.data['_meta']['_uuid_active'] = a.data['_id']
          a._set_parents()
          for i in a.data['parents'][a._class]:
            #match access with class parents
            p = cls(i, 'db')
            if not cls._user_has_access('put', p.data):
              return e403('Access denied for method put')
          a._set_access()
          a._insert_one()
          a._check_document_parents({'parents': {}})
          a._document_become_valid(cls)
          return a.json_one(), 201
