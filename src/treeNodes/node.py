ERROR_STRING = 'ERROR'

class TreeYalpNode(object):
  def __init__(self, type = '', size = 0, offset = 0) -> None:
    self.type = type
    self.size = size
    self.offset = offset
    self.errors = []
  
  def containsError(self):
    return self.type == ERROR_STRING or len(self.errors) > 0

  def addError(self, errorMessage):
    self.type = ERROR_STRING
    self.errors.append(errorMessage)

  def extendErrors(self, other):
    self.errors.extend(other.getErrors())

  def getErrors(self):
    return self.errors
