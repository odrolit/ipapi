from ipapi import app



class l():
  '''
  logging class
  '''
  def d(*args, **kwargs):
    '''
    log debug
    '''
    app.app.logger.debug(*args, **kwargs)
    l.dd()

  def i(*args, **kwargs):
    '''
    log info
    '''
    app.app.logger.info(*args, **kwargs)
    l.dd()

  def w(*args, **kwargs):
    '''
    log warning
    '''
    app.app.logger.warning(*args, **kwargs)
    l.dd()

  def e(*args, **kwargs):
    '''
    log error
    '''
    app.app.logger.error(*args, **kwargs)
    l.dd()
  
  def dd():
    '''
    log delimitier
    '''
    app.app.logger.debug('-'*30)
