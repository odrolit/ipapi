from .base import *



class user(base):
  """
  user class
  """
  
  IMPLICIT_PARENTS = True
  
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
    return g.user.find({'_meta._valid': True,
                     'scope': self.data['scope'],
                     '_bin._first': {'$lte': self.data['_bin']['_first']},
                     '_bin._last': {'$gte': self.data['_bin']['_last']}}, {'name': 1, })
  
  def _already_exists(self):
    '''
    returns True if already exists
    '''
    if self._find_one({'name': self.data['name'],
                       'prefix': self.data['prefix'],
                       'scope': self.data['scope']}):
      return True



class UserView(MethodView):
  '''
  API operations: get, post, put, delete
  '''
  method_decorators = []
  aaas = {}
  
  def get(self, **kwargs):
    try:
      return user.get(**kwargs)
    except Exception as e:
      return e400(e)
  
  def post(self):
    return user.post(request.json)

  
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
    return user.delete(_id, request.json)

  
  def search(self, **kwargs):
    return user.get(**kwargs)
    #NOTE: we need to wrap it with list for Python 3 as dict_values is not JSON serializable
    return list(self.aaas.values())[0:limit]

