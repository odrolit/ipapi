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
  
  def _C_M_get_active(self):
    '''
    returns active document or None,
    the document can be valid or deleted
    '''
    log.d(('_C_M_get_active'))
    r = self._find_one({'_meta._active': True,
                        'name': self.data['name'],
                        'prefix': self.data['prefix'],
                        'scope': self.data['scope']})
    return r
  
  def _C_M_get_active_valid_parents(self):
    '''
    returns list containing direct active
    and valid parents or root document
    '''
    log.d(('_C_M_get_active_valid_parents'))
    r = g.ipv4.find({'_meta._active': True,
                     '_meta._valid': True,
                     'scope': self.data['scope'],
                     '_bin._first': {'$lte': self.data['_bin']['_first']},
                     '_bin._last': {'$gte': self.data['_bin']['_last']}}, {'name': 1, })
    return r.sort('prefix', ASCENDING).limit(1)
  
  def _I_P_is_leaf(self):
    '''
    returns True if self is leaf
    '''
    log.d(('_I_P_is_leaf'))
    if self.data['prefix'] == 32:
      return True
  
  def _I_P_is_parent_of(self, child):
    '''
    returns True if self is parent of child
    '''
    log.d(('_I_P_is_parent_of'))
    return self.data['scope'] == child['scope'] and \
      self.data['prefix'] < child['prefix'] and \
      self.data['_bin']['_first'] <= child['_bin']['_first'] and \
      self.data['_bin']['_last'] >= child['_bin']['_last']
  
  def _I_P_is_equal_to(self, second):
    '''
    returns True if self equals to second
    '''
    log.d(('_I_P_is_equal_to'))
    return self.data['scope'] == second['scope'] and \
      self.data['name'] == second['name'] and \
      self.data['prefix'] == second['prefix']
  
  
  def _C_O_parent_added(self, parent):
    '''
    custom handling when parent was added
    
    expects parent instance as parameter
    '''
    log.d(('_C_O_parent_added', self._class, self.data['_id'],
           parent._class, parent.data['_id']))
    if parent._class == 'ipv4_whitelist':
      #blackholed IP can not be whitelisted
      if any(i in self.data['parents'] for i in ('ipv4_blackhole',
                                                 'ipv4_blackhole_add', 'ipv4_blackhole_del')):
        raise Exception(f'can not add {self.data[_id]} to whitelist, is blackholed')
    elif parent._class in ('ipv4_blackhole',
                           'ipv4_blackhole_add',
                           'ipv4_blackhole_del'):
      #whitelisted IP can not be blackholed
      if self.data['parents']['ipv4_whitelist']:
        raise Exception(f'can not add {self.data[_id]} to blackhole, is whitelisted')
      #only global scope can be blackholed
      if self.data['scope'] != 'global':
        raise Exception(f'can not add {self.data[_id]} to blackhole, not global')
    #TODO move to ipv4_blackhole._C_O_child_added()
    if parent._class == 'ipv4_blackhole':
      ipv4_blackhole_add(parent_id, self.data['name'], self.data['prefix'])
  
  def _C_O_parent_deleted(self, parent):
    '''
    custom handling when parent was deleted
        
    expects parent instance as parameter
    '''
    log.d(('_C_O_parent_deleted', self._class, self.data['_id'],
           parent._class, parent.data['_id']))
    #TODO move to ipv4_blackhole._C_O_child_deleted()
    if parent._class == 'ipv4_blackhole':
      ipv4_blackhole_add(parent_id, self.data['name'], self.data['prefix'])



class Ipv4View(MethodView):
  '''
  API operations: get, post, delete, put, patch
  '''
  method_decorators = []
  aaas = {}
  
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
  
  def delete(self, **kwargs):
    try:
      return ipv4.delete(**kwargs)
    except Exception as e:
      return e400(e)
  
  def put(self, **kwargs):
    try:
      return ipv4.put(**kwargs)
    except Exception as e:
      return e400(e)
    id = int(id)
    if id in self.aaas:
      aaa = self.aaas[id]
    else:
      aaa = {'id': id}
      self.aaas[id] = aaa
    aaa['name']  = request.json.get('name'),
    aaa['tag']  = request.json.get('tag'),
    aaa['time']  = datetime.now()
    return aaa, 201
  
  def search(self, **kwargs):
    return ipv4.get(**kwargs)
    #NOTE: we need to wrap it with list for Python 3 as dict_values is not JSON serializable
    return list(self.aaas.values())[0:limit]

