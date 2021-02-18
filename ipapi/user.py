from .base import *



class user(base):
  """
  user class
  
  each user has access defined in list
    data['parents']['access']
  
  each item has access defined in lists
    data['access']['get']
    data['access']['post']
    data['access']['patch']
    data['access']['put']
    data['access']['delete']
  """
  


class UserView(MethodView):
  '''
  API operations: get, post, delete, put, patch
  '''
  
  def get(self, **kwargs):
    try:
      return user.get(**kwargs)
    except Exception as e:
      return e400(e)
  
  def post(self):
    try:
      return user.post(request.json)
    except Exception as e:
      return e400(e)
  
  def patch(self):
    try:
      return user.patch(request.json)
    except Exception as e:
      return e400(e)
  
  def delete(self):
    try:
      return user.delete(request.json)
    except Exception as e:
      return e400(e)
  
  def put(self):
    try:
      return user.put(request.json)
    except Exception as e:
      return e400(e)
  
  def search(self, **kwargs):
    return user.get(**kwargs)
    #NOTE: we need to wrap it with list for Python 3 as dict_values is not JSON serializable
    return list(self.aaas.values())[0:limit]

