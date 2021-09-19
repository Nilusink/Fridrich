#! /usr/bin/python3.10
from struct import unpack, pack
import argparse
import socket
import json
import os
import time


def get_local_ip() -> str:
    """Try to determine the local IP address of the machine."""
    sock = socket.socket()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Use Google Public DNS server to determine own IP
        sock.connect(('8.8.8.8', 80))

        return sock.getsockname()[0]
    except socket.error:
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return '127.0.0.1'
    finally:
        sock.close() 


def main() -> None:
    """
    main program
    """
    parser = argparse.ArgumentParser(description='Send and receive files over the local network')
    parser.add_argument('mode', help="either 's' | 'send' or 'r' | 'receive'")
    parser.add_argument("-f", "--filename", required=False, help="filename for sending files")
    parser.add_argument("-d", "--destination", required=False, help="ip/hostname of destination computer")
    parser.add_argument("-np", "--no-print", required=False, action='store_true', help="if used disables the print function when receiving")
    args = parser.parse_args()

    if args.mode in ('r', 'receive'):
        hn = socket.gethostname()
        print(f'IP: {get_local_ip()}, HOSTNAME: {hn}', end='\r')
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
            (length,) = unpack('>Q', bs)
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

                if not args.no_print:
                    print(f'receiving [{len(data)}/{length}]                            ', end='\r')
            print(f'receiving took {time.time()-start} sec.')

            filename = resp['filename']
            print(f'Received "{filename}" (size={len(data)}) from "{address[0]}" ({socket.gethostbyaddr(address[0])[0]})')

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

    elif args.mode in ('s', 'send'):
        file_content = open(args.filename, 'rb').read()

        length = pack('>Q', len(file_content))

        msg = {
            "type": "file",
            "filename": args.filename.split('/')[-1]
        }

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((args.destination, 15151))  # connect to server

        server.sendall(json.dumps(msg).encode('utf-8'))
        server.recv(1024)
        server.sendall(length)
        server.sendall(file_content)
        print('done')
    
    else:
        raise ValueError(f"invalid parameter 'mode' with value '{args.mode}'")


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
        hn = socket.gethostname()
        print(f'IP: {get_local_ip()}, HOSTNAME: {hn}', end='\r')
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
            (length,) = unpack('>Q', bs)
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
            print(f'Received "{filename}" (size={len(data)}) from "{address[0]}" ({socket.gethostbyaddr(address[0])[0]})')

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

        length = pack('>Q', len(file_content))

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


if __name__ == '__main__':
    main()
