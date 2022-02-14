"""
for sending and receiving files from a remote host.

Author:
Nilusink
"""
from concurrent.futures import ThreadPoolExecutor, Future
import socket
import struct
import time
import json
import os

download_progress: float = 0.0
download_program: str = ""

executor = ThreadPoolExecutor()


def send_receive(mode: str, filename: str | None = ..., destination: str | None = ..., print_steps: bool | None = False,
                 download_directory: str | None = ..., thread: bool | None = False, overwrite: bool | None = False
                 ) -> None | Future:
    """
    send and receive files (function version)

    :param mode: either 's' | 'send' or 'r' | 'receive'
    :param filename: filename for sending files
    :param destination: ip/hostname of destination computer
    :param print_steps: enables print function when receiving
    :param download_directory: where the downloaded files should end up
    :param thread: if the program should be executed as a thread or not
    :param overwrite: if true overwrites output file
    :return: None of Future instance of the Thread
    """
    global download_progress, download_program
    if thread:
        return executor.submit(send_receive, mode=mode, filename=filename, destination=destination,
                               print_steps=print_steps, download_directory=download_directory, thread=False,
                               overwrite=overwrite)

    if mode in ('r', 'receive'):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 15151))
        server.listen()

        client, address = server.accept()
        resp = json.loads(client.recv(1024).decode('utf-8'))
        download_program = resp["filename"]
        client.send('received'.encode('utf-8'))

        # receiving data
        if resp['type'] == "file":
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

                download_progress = len(data)/length

                if to_read == o_to_read:    # check if new packages were received
                    no_rec += 1
                else:
                    no_rec = 0

                if no_rec >= 100:          # if for 100 loops no packages were received, raise connection loss
                    raise socket.error('Failed receiving data - connection loss')

                if print_steps:
                    print(f'\rreceiving [{len(data)}/{length}]')

            if print_steps:
                print(f'receiving took {time.time()-start} sec.')

            filename = resp['filename']

            i = 0
            if not overwrite:
                print("not overwriting")
                while os.path.isfile(filename):  # check if file with the same name already exists
                    i += 1
                    parts = filename.split('.')
                    filename = (parts[0].rstrip(str(i-1))+str(i)+'.')+'.'.join(parts[1::])

                if filename != resp['filename']:
                    print(f'renamed file from "{resp["filename"]}" to "{filename}"')

            if download_directory is not ...:
                filename = download_directory+'/'+filename

            with open(filename, 'wb') as out:
                out.write(data)
            client.send("done".encode())
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
        resp = str()
        while resp != "done":
            resp = server.recv(1024).decode()
            if resp != "done":
                print(f"invalid response: {resp}")

    else:
        raise ValueError(f"invalid parameter 'mode' with value '{mode}'")
