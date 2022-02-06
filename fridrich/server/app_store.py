from fridrich.file_transfer import send_receive
from fridrich.server.classes import User
import json
import os


def get_list() -> list:
    """
    :return: a list of available apps with versions
    """
    with open("/home/pi/Server/fridrich/server/settings.json", 'r') as inp:
        directory = json.load(inp)["AppStoreDirectory"]

    apps = list()
    for app in [dire for dire in os.listdir(directory) if os.path.isdir(directory + '/' + dire)]:
        size = float()
        filenames = [file for file in os.listdir(directory+app) if file.endswith(".zip")]
        if "AppInfo.json" not in os.listdir(directory+app):
            continue

        for filename in filenames:
            size += os.path.getsize(directory+app+'/'+filename)

        app_info = json.load(open(directory+app+'/AppInfo.json'))
        app_info["name"] = app
        app_info["files"] = filenames
        app_info["size"] = size
        apps.append(app_info)

    return apps


def send_apps(_message: dict, user: User) -> None:
    """
    :param _message: the message received from the client (not used)
    :param user: the user to send the answer to
    :return: None
    """
    user.send(get_list())


def download_app(message: dict, user: User) -> None:
    """
    :param message: the message received from the client (for the timestamp)
    :param user: the user to send the answer to
    :return: None
    """
    with open("/home/pi/Server/fridrich/server/settings.json", 'r') as inp:
        directory = json.load(inp)["AppStoreDirectory"]

    files = tuple((file for file in os.listdir(directory+message["app"]) if file.endswith(".zip")))

    user.send(files)
    for file in files:
        send_receive(mode="send", filename=directory+message["app"]+'/'+file, destination=user.ip, print_steps=False)


def receive_app(message: dict, user: User, modify: bool | None = False) -> None:
    """
    :param message: the message received from the client (for the timestamp)
    :param user: the user to send the answer to
    :param modify: if true used for modifying apps
    :return: None
    """
    with open("/home/pi/Server/fridrich/server/settings.json", 'r') as inp:
        directory = json.load(inp)["AppStoreDirectory"]+message["name"]

    if not modify:
        if os.path.isdir(directory):
            files = os.listdir(directory)
            if "AppInfo.json" in files:  # check if directory is empty, else send error
                user.send({"error": "ValueError", "info": f"App with name {message['name']} already exists"})
                return
            else:
                if len(files) != 0:
                    for element in files:
                        os.remove(directory+'/'+element)
        else:
            os.system(f"mkdir {directory}")

        with open(directory+"/AppInfo.json", 'w') as out:
            json.dump({
                       "version": message["version"],
                       "info": message["info"],
                       "publisher": user.name,
                       "publisher_id": user.id
            }, out, indent=4)

    user.send({"success": True})

    for _ in message["files"]:
        send_receive(mode='receive', print_steps=False, download_directory=directory, thread=False, overwrite=True)


def modify_app(message: dict, user: User) -> None:
    """
            msg = {
            "type": "modify_app",
            "o_name": old_app_name,
            "name": app_name,
            "version": app_version,
            "info": app_info,
            "new": [file.split("/").split("\\")[-1] for file in files],
            "to_delete": to_delete
    """
    try:
        app = {app["name"]: app for app in get_list()}[message["o_name"]]
    except KeyError:
        user.send({
                "error": f"App {message['o_name']} doesn't exist"
            })
        return

    if app["publisher_id"] != user.id:
        user.send({
                "error": f"App can only be modified by creator! {app['publisher']}"
            })
        return

    if app["publisher"] != user.name:
        app["publisher"] = user.name

    with open("/home/pi/Server/fridrich/server/settings.json", 'r') as inp:
        directory = json.load(inp)["AppStoreDirectory"]

    with open(directory+"/"+app["name"]+"/AppInfo.json", 'w') as out:
        print(f"before: {app}")
        tmp = {
            "version": "nAn",
            "info": message["info"],
            "publisher": user.name,
            "publisher_id": app["publisher_id"]
        }
        print(f"after: {tmp}")
        json.dump(tmp, out, indent=4)

    for file in message["to_remove"]:
        os.remove(directory+'/'+app['name']+'/'+file)

    if message["name"] != app["name"]:
        os.system(f"mv {directory+'/'+app['name']+'/'} {directory+'/'+message['name']+'/'}")

    receive_app(message, user, modify=True)

    with open(directory+"/"+app["name"]+"/AppInfo.json", 'w') as out:
        tmp = {
            "version": message["version"],
            "info": message["info"],
            "publisher": user.name
        }
        json.dump(tmp, out, indent=4)
