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

  def _get_parents(self):
    '''
    returns list containing direct parents or root document
    TODO
    '''
    return g.ipv4.find({'_meta._valid': True,
                     'scope': self.data['scope'],
                     '_bin._first': {'$lte': self.data['_bin']['_first']},
                     '_bin._last': {'$gte': self.data['_bin']['_last']}}, {'name': 1, })
  
  def _save(self):
    '''
    saves document and returns _id
    '''
    return g.ipv4.insert_one(self.data).inserted_id
  
  def _already_exists(self):
    '''
    returns True if already exists
    '''
    if self._find_one({'name': self.data['name'],
                       'prefix': self.data['prefix'],
                       'scope': self.data['scope']}):
      return True



class Ipv4View(MethodView):
  '''
  API operations: get, post, put, delete
  '''
  method_decorators = []
  aaas = {}
  
  def get(self, **kwargs):
    return ipv4.get(**kwargs)
  
  def post(self):
    try:
      return ipv4(request.json).post()
    except Exception as e:
      return e400(e)
  
  def put(self, id):
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
  
  def delete(self, _id):
    return ipv4.delete(_id, request.json)
    return ipv4(_id, 'db').delete()
  
  def search(self, **kwargs):
    return ipv4.get(**kwargs)
    #NOTE: we need to wrap it with list for Python 3 as dict_values is not JSON serializable
    return list(self.aaas.values())[0:limit]
