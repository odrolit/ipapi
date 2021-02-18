from .base import *



class access(base):
  """
  access class
  
  each user has access defined in list
    data['parents']['access']
  
  each item has access defined in lists
    data['access']['get']
    data['access']['post']
    data['access']['patch']
    data['access']['put']
    data['access']['delete']
  """
  
  def _C_O_child_added(self, child):
    '''
    custom handling when child was added
    
    expects child instance as parameter
    '''
    log.d((rid(), now(), '_C_O_child_added', self._class, self.data['_id'],
           child._class, child.data['_id']))
    #user must have put access to avoid privilege escalation
    if child._class == 'user' and not self._user_has_access('put', self.data):
      log.e((rid(), now(), '_C_O_child_added', self._class, self.data['_id'],
            child._class, child.data['_id']))
      raise Exception('_C_O_child_added user privilege escalation')



class AccessView(MethodView):
  '''
  API operations: get, post, delete, put, patch
  '''
  
  def get(self, **kwargs):
    try:
      return access.get(**kwargs)
    except Exception as e:
      return e400(e)
  
  def post(self):
    try:
      return access.post(request.json)
    except Exception as e:
      return e400(e)
  
  def patch(self):
    try:
      return access.patch(request.json)
    except Exception as e:
      return e400(e)
  
  def delete(self):
    try:
      return access.delete(request.json)
    except Exception as e:
      return e400(e)
  
  def put(self):
    try:
      return access.put(request.json)
    except Exception as e:
      return e400(e)
  
  def search(self, **kwargs):
    return access.get(**kwargs)
    #NOTE: we need to wrap it with list for Python 3 as dict_values is not JSON serializable
    return list(self.aaas.values())[0:limit]

