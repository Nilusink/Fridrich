"""
The fridrich module is a set of scripts used
to drive a Server, which is used mainly for
the Votings (There is much more to this,
but it's not really easy to explain),
and a Client that connects to the Server

Author:
Nilusink
"""


STORAGE_SIZES: tuple = (
    "b", "Mb", "Kb", "Gb", "Tb", "Pb", "Eb", "Zb", "Yb"
)


###########################################################################
#                  classes and functions used everywhere                  #
###########################################################################
def decorate_class(decorator, dont_decorate: list = ()):
    """
    decorate all methods of a class with one decorator
    """

    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and attr not in dont_decorate:
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate


def bytes_to_readable(n: int, rnd: int = 2) -> str:
    num_shrunk = 0
    while n > 1024 and num_shrunk < len(STORAGE_SIZES)-1:
        num_shrunk += 1
        n /= 1024

    return f"{round(n, rnd)} {STORAGE_SIZES[num_shrunk]}"


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
