from .base import *



class ipv4(base):
  """
  ipv4 class
  """
  
  def __init__(self, data, data_source = 'request'):
    '''
    puts data to self.data and sets object properties
    
    data_source can be request or database
    '''
    super().__init__(data, data_source)
  
  def _get_parents(self):
    '''
    returns list containing direct parents or root document
    TODO
    '''
    return [g.ipv4.find_one({'_meta._valid': True, 'name': '0.0.0.0/0'})]
  
  def _save(self):
    '''
    saves document
    '''
    g.ipv4.insert_one(self.data)
    log.i(self.data)


class Ipv4View(MethodView):
  '''
  API operations: get, post, put, delete
  '''
  method_decorators = []
  aaas = {}
  
  def get(self, _id):
    return ipv4.get(_id)
  
  def post(self):
    return ipv4(request.json).post()
    return ipv4.post(request.json)
    a = ipv4(request.json)
    return a.data, 201
  
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
  
  def delete(self, id):
    id = int(id)
    if id not in self.aaas:
      return NoContent, 404
    self.aaas.pop(id)
    return NoContent, 204
  
  def search(self, limit=100):
    return ipv4.get()
    #NOTE: we need to wrap it with list for Python 3 as dict_values is not JSON serializable
    return list(self.aaas.values())[0:limit]

