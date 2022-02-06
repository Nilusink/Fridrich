"""
All fridrich errors

Author:
Nilusink
"""


###########################################################################
#                              Error Classes                              #
###########################################################################
class ServerError(Exception):
    pass


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


class SecurityClearanceNotSet(Exception):
    pass


class MessageError(Exception):
    pass


class InvalidStringError(Exception):
    pass


class NetworkError(Exception):
    pass


class Error(Exception):
    pass
