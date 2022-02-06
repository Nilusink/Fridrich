"""
server sub-module
Contains all the modules that only the server needs

Author: Nilusink
"""
from fridrich.server.classes import *
from dataclasses import dataclass
from sys import platform
from os import system
import contextlib
import traceback
import datetime
import typing
import socket
import types
import time
import json
import os


@dataclass(init=False)
class Constants:
    """
    All constants (modify in file settings.json)
    """
    port: int | None = ...
    ip: str | None = ...
    Terminate: bool | None = ...

    direc: str | None = ...

    lastFile: str | None = ...
    nowFile: str | None = ...
    strikeFile: str | None = ...

    logDirec: str | None = ...

    CalFile: str | None = ...
    crypFile: str | None = ...
    versFile: str | None = ...
    tempLog: str | None = ...
    doubFile: str | None = ...
    SerlogFile: str | None = ...
    SerUpLogFile: str | None = ...
    ChatFile: str | None = ...
    VarsFile: str | None = ...
    WeatherDir: str | None = ...

    logFile: str | None = ...
    errFile: str | None = ...
    tempFile: str | None = ...

    DoubleVotes: int | None = ...

    DoubleVoteResetDay: str | None = ...
    switchTime: str | None = ...
    rebootTime: str | None = ...
    status_led_pin: int | None = ...
    status_led_sleep_time: list | None = ...

    AppStoreDirectory: str | None = ...

    def __init__(self) -> None:
        """
        create instance
        """
        # get variable values
        try:
            self.dic = json.load(open(os.getcwd() + '/config/settings.json', 'r'))

        except FileNotFoundError:
            self.dic = json.load(open('/home/apps/Fridrich/config/settings.json', 'r'))

        for Index, Value in self.dic.items():
            setattr(self, Index, Value)

    def __getitem__(self, item) -> str | int | bool:
        return self.dic[item]


class Debug:
    """
    for debugging...
    """
    instance: "Debug" = None

    # if a instance already exists, pass that one
    def __new__(cls, *args, **kw):
        if cls.instance is not None:
            print("old instance!")
            return cls.instance

        cls.instance = super(Debug, cls).__new__(cls)
        return cls.instance

    def __init__(self, deb_file: str, error_file: str) -> None:
        """
        debFile: file to write debug-messages to
        """
        self.file = deb_file
        self.errFile = error_file

        with open(self.file, 'w') as out:
            out.write('')

        with open(self.errFile, 'a') as out:
            out.write(
                f'\n\n\n\n\n######## - Program restart [{datetime.datetime.now().strftime("%Y.%m.%d at %H:%M:%S.%f")}] - ########\n\n')

    def debug(self, *args) -> None:
        """
        prints and writes all arguments

        for each argument a new line in the file is begun
        """
        print(*args)
        with open(self.file, 'a') as out:
            for element in args:
                out.write(str(element) + '\n')

    def catch_traceback(self, func: types.FunctionType) -> typing.Callable:
        """
        execute function with traceback and debug all errors
        """

        def wrapper(*args, **kw) -> None:
            try:
                if func.__name__ != "auto_reboot":
                    print(f"executing function: {func.__name__=}")
                return func(*args, **kw)
            except Exception as e:
                err = f'\n\n\n######## - Exception "{e}" on {datetime.datetime.now().strftime("%H:%M:%S.%f")} - ########\n\n{traceback.format_exc()}\n\n######## - END OF EXCEPTION - ########\n\n\n'
                self.debug(err)

        return wrapper

    def write_traceback(self, error: type, from_user: str | None = ...) -> None:
        """
        write a caught error
        """
        err = '\n\n\n' + (
            "From User: " + from_user if from_user is not ... else "") + f'######## - Exception "{error}" on {datetime.datetime.now().strftime("%H:%M:%S.%f")} - ########\n\n{traceback.format_exc()}\n\n######## - END OF EXCEPTION - ########\n\n\n'
        self.debug(err)


def send_success(user: User) -> None:
    """
    send the success message to the client
    """
    user.send({'Success': 'Done'})


def check_if(s: str, d: dict, voting: str) -> str:
    """
    if the name is already in the dict, return the name in the dict

    else return the given name ("s")
    """
    if voting in d:
        d = d[voting]
        keys = [d[key] for key in d] + ['Lukas', 'Melvin',
                                        'Niclas']  # keys is (ex.) ['Fridrich', 'Lukas', 'Melvin', 'Niclas]

        for element in keys:
            if s.lower().replace(' ', '') == element.lower().replace(' ', ''):
                return element
        return s
    return s


def get_new_ones(flag: str, vote_instance: FileVar, last_file: str, voting: str) -> list:
    """
    get all attendants which are not in the default name list
    """
    new_ones = list()
    tmp: dict
    match flag:
        case 'now':
            tmp = vote_instance.get()
        case 'last':
            tmp = json.load(open(last_file, 'r'))
        case _:
            raise ValueError(f'"{flag}" is not an option')

    for element in tmp[voting]:
        if not tmp[voting][element] in ['Lukas', 'Niclas', 'Melvin'] + new_ones:
            new_ones.append(tmp[voting][element])

    return new_ones


def reboot() -> None:
    if platform == "win32":
        system("shutdown -r -t 0")
        return
    system("sudo reboot")


class Chat:
    """
    Handler for Chat file
    """

    @staticmethod
    def add(message: str, from_user: str) -> None:
        """
        append a message to the file
        """
        mes = Chat.get()  # get message list from file

        curr_time = datetime.datetime.now()
        formatted_time = curr_time.strftime('%H:%M:%S.%f') + time.strftime(' - %d.%m.%Y')
        mes.append({'time': formatted_time, 'content': message, 'user': from_user})  # append message
        json.dump(mes, open(Const.ChatFile, 'w'), indent=4)  # write message

    @staticmethod
    def get() -> list:
        """
        get all messages
        """
        try:
            mes = json.load(open(Const.ChatFile, 'r'))  # try to read file
        except FileNotFoundError:
            mes = list()  # if file doesn't exist, create new list
        return mes


class Communication:
    """
    Handler for server side communication between Server and Client
    """

    @staticmethod
    def send(client: socket.socket, message: dict | list, encryption=None, key=None) -> None:
        """
        send message to client
        """
        stringMes = json.dumps(message, ensure_ascii=False)
        print(stringMes)
        if encryption:
            mes = encryption(stringMes, key=key)
            # print(mes)
            with contextlib.suppress(OSError, AttributeError):
                client.send(mes)
                print(f'sent to client: {mes}')
            print('failed to send')
            return

        with contextlib.suppress(OSError, AttributeError):
            print(f'sent to client ({client}): {stringMes.encode("utf-8")}')
            client.send(stringMes.encode('utf-8'))

    @staticmethod
    def receive(server: socket.socket, debugging_method, keys: list | typing.Generator) -> typing.Tuple[
                                                                                               socket.socket, str] | \
                                                                                           typing.Tuple[
                                                                                               None, None] | bool:
        """
        receive message from client
        """
        # Accept Connection
        try:
            client, address = server.accept()
            del address
            # debug.debug(f'Connected to {address}')
        except OSError:
            return False
        # try to load the message, else ignore it and restart
        mes = client.recv(2048)
        mes = cryption_tools.try_decrypt(mes, keys)

        if not mes:
            debugging_method('Message Error')
            with contextlib.suppress(AttributeError):
                Communication.send(client, {'Error': 'MessageError', 'info': 'Invalid Message/AuthKey'})
                client.close()
            return None, None
        return client, mes


Const = Constants()
DEBUGGER = Debug(Const.SerlogFile, Const.errFile)
