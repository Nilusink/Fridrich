"""
Handler for the AppStore  (server)
"""
from fridrich import new_types
import json
import os


def get_list(directory: str | None = ...) -> list:
    """
    :param directory: the directory where the apps are saved
    :return: a list of available apps with versions
    """
    if directory is ...:
        directory = os.getcwd()+'\\Apps\\'

    apps = list()
    for app in os.listdir(directory):
        size = float()
        filenames = [file for file in os.listdir(directory+app) if file.endswith(".zip")]
        for filename in filenames:
            size += os.path.getsize(directory+app+'/'+filename)

        app_info = json.load(open(directory+app))
        apps.append({
            "name": app,
            "version": app_info["version"],
            "files": filenames,
            "size": size
        })
    return apps


def send_apps(message: dict, user: new_types.User) -> None:
    """
    :param message: the message received from the client (for the timestamp)
    :param user: the user to send the answer to
    :return: None
    """
    msg = {
        "content": get_list(),
        "time": message["time"]
    }
    user.send(msg)
