from fridrich.server.server_funcs import send_success
from fridrich.new_types import User
from fridrich.server import Const
from time import strftime


def ping(message: dict, user: User, *_args) -> None:
    """
    immediately send back a message (to measure latency)
    """
    send_success(user, message)


def get_time(message: dict, user: User, *_args) -> None:
    """
    get the current server time
    """
    msg = {
        "content": {
            "now": strftime("%H:%M:%S"),
            "voting": Const.switchTime
        },
        "time": message["time"]
    }
    user.send(msg)
