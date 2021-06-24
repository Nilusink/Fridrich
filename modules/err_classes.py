# file for error classes
class AccessError(Exception):
    pass
class AuthError(Exception):
    pass

class JsonError(Exception):
    pass

class NoVotes(Exception):
    pass

class UnknownError(Exception):
    pass

class RegistryError(Exception):
    pass

class NotAUser(Exception):
    pass

class InvalidRequest(Exception):
    pass

class SecutiryClearanceNotSet(Exception):
    pass