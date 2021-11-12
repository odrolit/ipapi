from .base import *



class ipv4(base):
  """
  ipv4 class
  """
  
  IMPLICIT_PARENTS = True
  
  def __init__(self, data, data_source = 'request'):
    '''
    puts data to self.data and sets object properties
    
    data_source can be request or database
    '''
    super().__init__(data, data_source)
    
    log.d((rid(), now(), '__init__', self._class, self.data_source, data))
    n = IPv4Network(f'{self.data["name"]}/{self.data["prefix"]}')
    #check request
    if self.data_source == 'request':
      if self.data['scope'] == 'global' and not n.is_global:
        raise AttributeError('Not global address')
    #do not check db
    if self.data_source != 'db':
      #bin hook for search efficiency
      self.data['_bin'] = {}
      self.data['_bin']['_first'] = n.network_address.packed
      self.data['_bin']['_last'] = n.broadcast_address.packed
    log.d((rid(), now(), '__init__', self._class, self.data_source, data))
  
  def _C_U_get_active(self):
    '''
    returns active document or None,
    the document can be valid or deleted
    '''
    log.d((rid(), now(), '_C_U_get_active'))
    r = self._find_one({'_meta._active': True,
                        'scope': self.data['scope'],
                        '_bin._first': self.data['_bin']['_first'],
                        '_bin._last': self.data['_bin']['_last']})
    log.d((rid(), now(), '_C_U_get_active', r))
    return r
  
  def _C_U_get_active_valid_parents(self):
    '''
    returns list containing direct active
    and valid parents or root document
    
    at 200k addresses new PUT takes:
    - 3600 ms using index(200k), sort(2), limit(1)
    - 900 ms using index(200k).hint(index).sort(2).limit(1)
    - 600 ms using index(200k).hint(index) and manual iteration
    '''
    log.d((rid(), now(), '_C_U_get_active_valid_parents'))
    hint = '_meta._active_1__meta._valid_1_scope_1__bin._first_1__bin._last_1'
    r = self._find_multi_simple(
      {'_meta._active': True,
       '_meta._valid': True,
       'scope': self.data['scope'],
       '_bin._first': {'$lte': self.data['_bin']['_first']},
       '_bin._last': {'$gte': self.data['_bin']['_last']}},
      hint)
    prefix = 0
    for i in r:
      if i['prefix'] >= prefix:
        prefix = i['prefix']
        s = i
    #r.sort('prefix', ASCENDING).limit(1)
    #log.d((rid(), now(), '_C_U_get_active_valid_parents', r.count()))
    log.d((rid(), now(), '_C_U_get_active_valid_parents', s))
    return [s]
  
  def _I_P_is_leaf(self):
    '''
    returns True if self is leaf
    '''
    if self.data['prefix'] == 32:
      r = True
    else:
      r = False
    log.d((rid(), now(), '_I_P_is_leaf', r))
    return r
  
  def _I_P_is_parent_of(self, child):
    '''
    returns True if self is parent of child
    '''
    r = self.data['scope'] == child['scope'] and \
      self.data['prefix'] < child['prefix'] and \
      self.data['_bin']['_first'] <= child['_bin']['_first'] and \
      self.data['_bin']['_last'] >= child['_bin']['_last']
    log.d((rid(), now(), '_I_P_is_parent_of', r))
    return r
  
  def _C_O_parent_added(self, parent):
    '''
    custom handling when parent was added
    
    expects parent instance as parameter
    '''
    log.d((rid(), now(), '_C_O_parent_added', self._class, self.data['_id'],
           parent._class, parent.data['_id']))
    if parent._class == 'ipv4_protected':
      #nexthop IP can not be protected
      if any(i in self.data['parents'] for i in ('ipv4_nexthop',
                                                 'ipv4_nexthop_add', 'ipv4_nexthop_del')):
        log.e((rid(), now(), '_C_O_parent_added', self._class, self.data['_id'],
               parent._class, parent.data['_id']))
        raise Exception(f'can not add {self.data[_id]} to protected, is nexthop')
    elif parent._class in ('ipv4_nexthop',
                           'ipv4_nexthop_add',
                           'ipv4_nexthop_del'):
      #protected IP can not have nexthop
      if self.data['parents']['ipv4_protected']:
        log.e((rid(), now(), '_C_O_parent_added', self._class, self.data['_id'],
               parent._class, parent.data['_id']))
        raise Exception(f'can not add {self.data[_id]} to nexthop, is protected')
      #nexthop can be set only for global scope
      if self.data['scope'] != 'global':
        log.e((rid(), now(), '_C_O_parent_added', self._class, self.data['_id'],
               parent._class, parent.data['_id']))
        raise Exception(f'can not add {self.data[_id]} to nexthop, not global')
    #TODO move to ipv4_nexthop._C_O_child_added()
    if parent._class == 'ipv4_nexthop':
      ipv4_nexthop_add(parent_id, self.data['name'], self.data['prefix'])
    log.d((rid(), now(), '_C_O_parent_added', self._class, self.data['_id'],
           parent._class, parent.data['_id']))
  
  def _C_O_parent_deleted(self, parent):
    '''
    custom handling when parent was deleted
        
    expects parent instance as parameter
    '''
    log.d((rid(), now(), '_C_O_parent_deleted', self._class, self.data['_id'],
           parent._class, parent.data['_id']))
    #TODO move to ipv4_nexthop._C_O_child_deleted()
    if parent._class == 'ipv4_nexthop':
      ipv4_nexthop_del(parent_id, self.data['name'], self.data['prefix'])
    log.d((rid(), now(), '_C_O_parent_deleted', self._class, self.data['_id'],
           parent._class, parent.data['_id']))



class Ipv4View(MethodView):
  '''
  API operations: get, post, delete, put, patch
  '''
  
  def get(self, **kwargs):
    try:
      return ipv4.get(**kwargs)
    except Exception as e:
      return e400(e)
  
  def post(self):
    try:
      return ipv4.post(request.json)
    except Exception as e:
      return e400(e)
  
  def patch(self):
    try:
      return ipv4.patch(request.json)
    except Exception as e:
      return e400(e)
  
  def delete(self):
    try:
      return ipv4.delete(request.json)
    except Exception as e:
      return e400(e)
  
  def put(self):
    try:
      return ipv4.put(request.json)
    except Exception as e:
      return e400(e)
  
  def search(self, **kwargs):
    return ipv4.get(**kwargs)
    #NOTE: we need to wrap it with list for Python 3 as dict_values is not JSON serializable
    return list(self.aaas.values())[0:limit]

