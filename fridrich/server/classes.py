from fridrich import cryption_tools, decorate_class
from concurrent.futures import ThreadPoolExecutor
from fridrich.server.accounts import USER_CONFIG
from fridrich.classes import Daytime
from fridrich.server import DEBUGGER
from contextlib import suppress
from struct import pack
import socket
import typing
import time
import json


@decorate_class(DEBUGGER.catch_traceback())
class User:
    def __init__(self, name: str, sec: str, key: str, user_id: int, cl: socket.socket, ip: str, function_manager: typing.Callable, debugger) -> None:
        """
        :param name: Name of the client
        :param sec: security clearance
        :param key: encryption key of client
        :param cl: the users socket instance
        :param ip: the users host ip
        :param function_manager: the manager class for executing functions
        :param debugger: a instance of server_funcs.Debug
        """
        self.__name = name
        self.__sec = sec
        self.__key = key
        self.__id = user_id

        self.__client = cl
        self.__ip = ip
        self.manager = function_manager
        self.debugger = debugger

        self.__disconnect = False

        self.loop = True

        # message pool
        self.__message_pool_names: typing.Tuple[str, str] = ("", "")
        self.__message_pool: typing.Dict[str, typing.Any] = {}
        self.__message_pool_index: int = 0
        self.__message_pool_max: int = 0
        self.__message_pool_time: str = ""

        # for auto-disconnect
        self.__last_connection = Daytime.now()
        self.__timeout = Daytime(minute=5)  # if there wasn't any interaction with a client for 2 minutes, kick it (ping also counts as activity)
        self.__thread_pool = ThreadPoolExecutor(max_workers=2)

        # only if the user's security clearance requires auto-logout, start the thread
        if USER_CONFIG[self.sec]["auto_logout"]:
            self.__auto_logout_thread = self.__thread_pool.submit(self.__check_disconnect)

        # start to receive
        self.__thread_pool.submit(self.receive)

    @property
    def name(self) -> str:
        """
        :return: the username of the user
        """
        return self.__name

    @property
    def sec(self) -> str:
        """
        :return: the security clearance of the user
        """
        return self.__sec

    @property
    def ip(self) -> str:
        """
        :return: the users host-ip
        """
        return self.__ip

    @property
    def id(self) -> int:
        """
        :return: the users id
        """
        return self.__id

    @property
    def disconnect(self) -> bool:
        return self.__disconnect

    def receive(self) -> None:
        """
        needs to be run in a thread, handles communication with client
        """
        self.__client.settimeout(.2)
        while self.loop:
            try:
                mes = cryption_tools.MesCryp.decrypt(self.__client.recv(2048), self.__key.encode())

                # refresh auto-disconnect
                self.__last_connection = Daytime.now()

                mes = json.loads(mes)

                # create message pool for request
                self.__message_pool_names = tuple(func_name["f_name"] if "f_name" in func_name else func_name["type"] for func_name in mes["content"])
                self.__message_pool_max = len(mes["content"])
                self.__message_pool_time = mes["time"]
                self.__message_pool_index = 0

                if not mes or mes is None:
                    self.send({'Error': 'MessageError', 'info': 'Invalid Message/AuthKey'}, message_type="Error", force=True)
                    continue

                for message in mes["content"]:
                    self.exec_func(message)

            except cryption_tools.NotEncryptedError:
                print("not encrypted")
                self.send({'Error': 'NotEncryptedError'}, message_type="Error", force=True)
                return

            except TimeoutError:
                continue

    def send(self, message: iter, message_type: str | None = 'function', force: bool | None = False) -> None:
        """
        save the message(s) for sending
        """
        message = {
            "content": message
        }
        if self.__message_pool_max == sum([0 if element is None else 1 for element in self.__message_pool]) and not force:
            print(f"Pool error: {self.__message_pool=}, {self.__message_pool_names=}, {message=}")
            raise IndexError("trying to send message but no pool index is out of range")

        message['type'] = message_type

        try:
            self.__message_pool[self.__message_pool_names[self.__message_pool_index]] = message
            self.__message_pool_index += 1

        except IndexError:  # if used with "force", appends the message in case of a IndexError (if the pool hasn't been created or something)
            if force:
                self.__message_pool["forced"] = message
            else:
                raise

        if force or self.__message_pool_index == self.__message_pool_max:   # aka all functions are done
            self._send()

    def _send(self) -> None:
        """
        actually send the message
        """
        # refresh auto-disconnect
        self.__last_connection = Daytime.now()

        # process the message
        mes = {
            "content": self.__message_pool,
            "time": self.__message_pool_time
        }
        stringMes = json.dumps(mes)
        mes = cryption_tools.MesCryp.encrypt(stringMes, key=self.__key.encode())
        length = pack('>Q', len(mes))   # get message length

        # send to client
        try:
            self.__client.sendall(length)
            self.__client.sendall(mes)

        except (OSError, ConnectionResetError, ConnectionAbortedError):
            return self.end()

        # reset message pool
        self.__message_pool = {}
        self.__message_pool_index = 0
        self.__message_pool_max = 0
        self.__message_pool_time = ""
        self.__message_pool_names = ()

    def __check_disconnect(self) -> None:
        """
        for auto-disconnect, check if there was no interaction with the user for self.__timeout
        """
        while self.loop:
            if Daytime.now()-self.__last_connection > self.__timeout:
                print(f"disconnecting {self.name}, last contact: {self.__last_connection}, now: {Daytime.now()} ({self.__timeout=})")
                return self.end("timeout")

            time.sleep(.2)

    def exec_func(self, message: dict):
        """
        execute functions for the client
        """
        try:
            self.manager(message, self)

        except Exception as e:
            self.debugger.write_traceback(e, from_user=self.name)
            return

    def end(self, reason: str = ...) -> None:
        print(f"Disconnecting: {self} {'('+reason+')' if reason is not ... else ''}, shutting down threads")
        self.__disconnect = True
        self.loop = False
        self.__client.close()
        self.__thread_pool.shutdown(wait=False)
        print(f"{self} is fully shut down and disconnected")

    def __getitem__(self, item) -> str:
        return dict(self)[item]

    def __iter__(self) -> typing.Iterator:
        for key, item in (('key', self.__key), ('name', self.__name), ('sec', self.__sec)):
            yield key, item

    def __str__(self) -> str:
        return f"<class User (name={self.__name}, sec={self.__sec})>"

    def __repr__(self) -> str:
        return self.__str__()

    def __contains__(self, item) -> bool:
        return item == self.name or item == self.id


@decorate_class(DEBUGGER.catch_traceback(raise_error=False), dont_decorate=["_garbage_collector"])
class UserList:
    def __init__(self, users: typing.List[User] | None = ...) -> None:
        """
        initialize a list for all users and start garbage-collector

        special: ´´get_user´´ function (gets a user by its name or encryption key)
        """
        self._users = users if users is not ... else list()

        self.executor = ThreadPoolExecutor()
        self.collector = self.executor.submit(self._garbage_collector, .5)

        self.loop = True

    @property
    def names(self) -> typing.Generator:
        """
        return the names of all users
        """
        for element in self._users:
            yield element.name

    def sendall(self, message: iter) -> None:
        for user in self._users:
            user.send({
                "time": time.time(),
                "content": message
            }, force=True)

    def append(self, obj: User) -> None:
        """
        append object to the end of the list and start receive thread
        """
        if obj.name in self and not USER_CONFIG[obj.sec]["multi_login_allowed"]:
            print(f"multi login disallowed, logging out other users")
            with suppress(KeyError):
                self.remove_by(name=obj.name)

        self._users.append(obj)

    def get_user(self, name: str | None = ..., user_id: str | None = ...) -> User:
        """
        get a user by its name or encryption key
        """
        for element in self._users:
            if name is not ...:
                if name in element:
                    return element

            if user_id is not ...:
                if user_id in element:
                    return element

        else:
            raise KeyError(f'No User with name {name} or id {user_id} found!')

    def remove(self, user: User) -> None:
        """
        remove a user by its class
        """
        user.end()
        self._users.remove(user)

    def remove_by(self, *args, **kw) -> None:
        """
        remove a user by its username or encryption key

        arguments are the same as for UserList.get_user
        """
        print("removing by")
        self.remove(self.get_user(*args, **kw))

    def reset(self) -> None:
        """
        reset all users (clear self._users)
        """
        for user in self._users:
            user.send({'warning': 'server_logout'}, message_type="disconnect", force=True)
            user.end()
        self._users = list()

    def _garbage_collector(self, time_between_loops: float | None = .5) -> None:
        """
        check if any of the clients is disconnected and if yes, remove it
        """
        while self.loop:
            for element in self._users:
                if element.disconnect:
                    print(f"removing {element.name}")
                    element.end()
                    self._users.remove(element)
            time.sleep(time_between_loops)

    def end(self) -> None:
        """
        shutdown all threads
        """
        self.loop = False
        for user in self._users:
            user.end()
        self.executor.shutdown(wait=False)

    def __iter__(self) -> typing.Iterator:
        for element in self._users:
            yield element

    def __contains__(self, other: str) -> bool:
        print("contains?")
        with suppress(KeyError):
            self.get_user(name=other, user_id=other)
            return True
        return False

    def __str__(self) -> str:
        return f"<class UserList (users={list(self.names)}, running={self.__bool__()})>"

    def __repr__(self) -> str:
        return self.__str__()

    def __bool__(self) -> bool:
        """
        return True if AuthKey
        """
        return self.loop


class FileVar:
    def __init__(self, value: str | dict, files: str | list | tuple) -> None:
        """
        create a variable synced to one or more files
        """
        # filter all items that are not a string
        self.files = [file if type(file) == str else ... for file in files] if type(files) in (list, tuple) else [files]
        # remove all non standard items
        while ... in self.files:
            self.files.remove(...)

        self.value = value
        self.type = type(value)

        self.set(value)  # assign variable

    def __repr__(self) -> str:
        self.get()
        return repr(self.value)

    def __len__(self) -> int:
        """
        return the length of ``self.value``
        """
        self.get()
        return len(self.value)

    def __str__(self) -> str:
        """
        return string of ``self.value``
        """
        self.get()
        return str(self.value)

    # str options
    def __add__(self, other: str) -> str:
        self.get()
        self.check_type(str)

        self.set(self.value + other)

        return self.value

    # dict options
    def __getitem__(self, key: str) -> typing.Any:
        """get an item if ``self.value`` is a dict
        """
        self.get()  # update variable in case something in the file has changed
        self.check_type(dict)
        if key not in self.value:
            raise KeyError(f'"{key}" not in dict "{self.value}"')
        return self.value[key]

    def __setitem__(self, key, value) -> dict:
        """
        set an item of a dict
        """
        self.get()
        self.check_type(dict)
        self.value[key] = value
        self.set(self.value)
        return self.value

    def __delitem__(self, key: str) -> None:
        self.get()
        self.check_type(dict)

        del self.value[key]

    def __iter__(self) -> typing.Iterator:
        self.get()
        self.check_type(dict)

        for key, item in self.value.items():
            yield key, item

    # general options
    def __eq__(self, other) -> bool:
        """
        check if the ``==`` given value is the same as either the whole class or the value
        """
        self.get()
        if type(other) == FileVar:
            return other.value == self.value and list(other.files) == list(self.files)

        return other == self.value

    def __contains__(self, other) -> bool:
        self.get()
        return other in self.value

    def set(self, value: str | dict) -> None:
        """
        set the variable (update files)
        """
        self.value = value
        self.type = type(value)

        for file in self.files:
            for _ in range(5):  # check five times if a file is already opened, if failed then pass
                try:
                    with open(file, 'w') as out:
                        if self.type == dict:
                            json.dump(self.value, out, indent=4)
                            break
                        out.write(self.value)
                        break

                except IOError:
                    time.sleep(.2)

                except json.JSONDecodeError:
                    with open(file, "w") as out_p:
                        json.dump({}, out_p)

            else:
                raise IOError(f"Can't access file {file}")

    def get(self) -> str | dict:
        """
        get the variable in its original type
        """
        file = self.files[0]
        for _ in range(5):
            try:
                with open(file, 'r') as inp:
                    try:
                        self.value = json.load(inp)

                    except json.JSONDecodeError:
                        self.value = inp.read()

                self.type = type(self.value)

                return self.value

            except IOError:
                time.sleep(.2)

            except json.JSONDecodeError:
                with open(file, "w") as out_p:
                    json.dump({}, out_p)

        else:
            raise IOError(f"Can't access file {file}")

    def check_type(self, wanted_type: typing.Type[str] | typing.Type[dict]) -> None:
        """
        if type is wrong, raise an error
        """
        if not self.type == wanted_type:
            raise TypeError(
                f'Expected {wanted_type}, got {self.type}. This function is not available for the given variable type')
