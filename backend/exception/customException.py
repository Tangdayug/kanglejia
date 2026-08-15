class UserNotFoundException(Exception):
   def __init__(self, message:str):
      self.message = message
class PasswordNotMatchException(Exception):
   def __init__(self, message:str):
      self.message = message
class TokenException(Exception):
   def __init__(self, message:str):
      self.message = message

class UserExistException(Exception):
   def __init__(self, message:str):
      self.message = message

class NotFoundException(Exception):
   def __init__(self, message:str):
      self.message = message
