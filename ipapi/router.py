from datetime import datetime
from connexion import NoContent
from flask import request
from flask.views import MethodView
from pprint import pprint



class RouterView(MethodView):
  '''
  API operations: get, post, put, delete
  '''
  method_decorators = []
  routers = {}
  
  def get(self, _id):
    _id = int(_id)
    if _id not in self.routers:
      return NoContent, 404
    return self.routers[_id]
  
  def post(self):
    pprint(request.json)
    router = {
      '_id': len(self.routers) + 1,
      'name': request.json.get('name'),
      'tag': request.json.get('tag'),
      'time': datetime.now()
    }
    self.routers[router['_id']] = router
    return router, 201
  
  def put(self, _id):
    _id = int(_id)
    if _id in self.routers:
      router = self.routers[_id]
    else:
      router = {'_id': _id}
      self.routers[_id] = router
    router['name']  = request.json.get('name'),
    router['tag']  = request.json.get('tag'),
    router['time']  = datetime.now()
    return router, 201
  
  def delete(self, _id):
    _id = int(_id)
    if _id not in self.routers:
      return NoContent, 404
    self.routers.pop(_id)
    return NoContent, 204
  
  def search(self, limit=100):
    return ipv4().get()
    #NOTE: return list for Python 3 as dict_values is not JSON serializable
    return list(self.routers.values())[0:limit]
