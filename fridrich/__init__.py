"""
The fridrich module is a set of scripts used
to drive a Server, which is used mainly for
the Votings (There is much more to this,
but it's not really easy to explain),
and a Client that connects to the Server

Author:
Nilusink
"""


###########################################################################
#                  classes and functions used everywhere                  #
###########################################################################
def decorate_class(decorator):
    """
    decorate all methods of a class with one decorator
    """
    ignored = ("__init__", "__new__")

    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and attr not in ignored:
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate


class ConsoleColors:
    """
    for better readability (colors) in the console
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
