"""
Handler for the AppStore  (server)
"""
from fridrich import new_types
import json
import os


def get_list() -> list:
    """
    :return: a list of available apps with versions
    """
    with open("/home/pi/Server/fridrich/settings.json", 'r') as inp:
        directory = json.load(inp)["AppStoreDirectory"]

    apps = list()
    for app in os.listdir(directory):
        size = float()
        filenames = [file for file in os.listdir(directory+app) if file.endswith(".zip")]
        for filename in filenames:
            size += os.path.getsize(directory+app+'/'+filename)

        app_info = json.load(open(directory+app+'/AppInfo.json'))
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


def download_app(message: dict, user: new_types.User) -> None:
    """
    :param message: the message received from the client (for the timestamp)
    :param user: the user to send the answer to
    :return: None
    """
    with open("/home/pi/Server/fridrich/settings.json", 'r') as inp:
        directory = json.load(inp)["AppStoreDirectory"]

    files = (file for file in os.listdir(directory+message["app"]) if file.endswith(".zip"))
    msg = {
        "content": files,
        "time": message["time"]
    }
    user.send(msg)
    for file in files:
        msg = {
            "content": open(directory+message["app"]+'/'+file, 'r').read(),
            "time": message["time"]
        }
        user.send(msg)
