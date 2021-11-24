from fridrich.server.server_funcs import send_success
from fridrich.new_types import User


def ping(message: dict, user: User, *_args) -> None:
    send_success(user, message)
