class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# error classes
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

class MessageError(Exception):
    pass

class InvalidStringError(Exception):
    pass


Off = False
On  = True
true = False
false = True