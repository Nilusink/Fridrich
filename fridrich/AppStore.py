"""
Handler for the AppStore  (server)
"""
from fridrich import new_types
import socket
import struct
import time
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
            "info": app_info["info"],
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

    files = tuple((file for file in os.listdir(directory+message["app"]) if file.endswith(".zip")))
    msg = {
        "content": files,
        "time": message["time"]
    }
    user.send(msg)
    for file in files:
        send_receive(mode="send", filename=directory+message["app"]+'/'+file, destination=user.ip, print_steps=False)


def send_receive(mode: str, filename: str | None = ..., destination: str | None = ..., print_steps: bool | None = False) -> None:
    """
    send and receive files (function version)

    :param mode: either 's' | 'send' or 'r' | 'receive'
    :param filename: filename for sending files
    :param destination: ip/hostname of destination computer
    :param print_steps: enables print function when receiving
    :return: None
    """

    if mode in ('r', 'receive'):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', 15151))
        server.listen()

        client, address = server.accept()
        resp = json.loads(client.recv(1024).decode('utf-8'))
        client.send('received'.encode('utf-8'))

        # receiving data
        if resp['type'] == "file":
            print(f'receiving {resp["filename"]}')
            bs = client.recv(8)
            (length,) = struct.unpack('>Q', bs)
            data = b''
            no_rec = 0
            to_read = 0
            start = time.time()
            while len(data) < length:
                # doing it in batches is generally better than trying
                # to do it all in one go, so I believe.
                o_to_read = to_read
                to_read = length - len(data)
                data += client.recv(
                                    4096 if to_read > 4096 else to_read
                                    )

                if to_read == o_to_read:    # check if new packages were received
                    no_rec += 1
                else:
                    no_rec = 0

                if no_rec >= 100:          # if for 100 loops no packages were received, raise connection loss
                    raise socket.error('Failed receiving data - connection loss')

                if print_steps:
                    print(f'receiving [{len(data)}/{length}]                            ', end='\r')
            print(f'receiving took {time.time()-start} sec.')

            filename = resp['filename']

            i = 0
            while os.path.isfile(filename):  # check if file with the same name already exists
                i += 1
                parts = filename.split('.')
                filename = parts[0].rstrip(str(i-1))+str(i)+'.'+parts[1]

            if filename != resp['filename']:
                print(f'renamed file from "{resp["filename"]}" to "{filename}"')

            with open(filename, 'wb') as out:
                out.write(data)

        else:
            print(f'Cannot receive of type "{resp["type"]}"')

    elif mode in ('s', 'send'):
        file_content = open(filename, 'rb').read()

        length = struct.pack('>Q', len(file_content))

        msg = {
            "type": "file",
            "filename": filename.split('/')[-1]
        }

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((destination, 15151))  # connect to server

        server.sendall(json.dumps(msg).encode('utf-8'))
        server.recv(1024)
        server.sendall(length)
        server.sendall(file_content)
        print('done')

    else:
        raise ValueError(f"invalid parameter 'mode' with value '{mode}'")
