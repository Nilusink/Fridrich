from concurrent.futures import ThreadPoolExecutor
from fridrich import cryption_tools
from struct import pack
import contextlib
import socket
import typing
import json
import time


class FileVar:
    def __init__(self, value: str | dict, files: str | list | tuple) -> None:
        """
        create a variable synced to one or more files
        """
        self.files = files if type(files) in (list, tuple) else [files]
        
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

        self.set(self.value+other)

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
            with open(file, 'w') as out:
                if self.type == dict:
                    json.dump(self.value, out, indent=4)
                    continue
                out.write(self.value)

    def get(self) -> str | dict:
        """
        get the variable in its original type
        """
        file = self.files[0]
        with open(file, 'r') as inp:
            try:
                self.value = json.load(inp)

            except json.JSONDecodeError: 
                self.value = inp.read()
        
        self.type = type(self.value)

        return self.value

    def check_type(self, wanted_type: typing.Type[str] | typing.Type[dict]) -> None:
        """
        if type is wrong, raise an error
        """
        if not self.type == wanted_type:
            raise TypeError(f'Expected {wanted_type}, got {self.type}. This function is not available for the given variable type')


class User:
    def __init__(self, name: str, sec: str, key: str, cl: socket.socket, function_manager) -> None:
        """
        ´´name´´: Name of the client
        ´´sec´´: security clearance
        ´´key´´: encryption key of client
        """
        self.name = name
        self.sec = sec
        self.key = key

        self.client = cl
        self.manager = function_manager

        self.disconnect = False

        self.loop = True

    def receive(self) -> None:
        """
        needs to be run in a thread, handles communication with client
        """
        while self.loop:
            try:
                mes = cryption_tools.MesCryp.decrypt(self.client.recv(2048), self.key.encode())

                if not mes or mes is None:
                    self.send({'Error': 'MessageError', 'info': 'Invalid Message/AuthKey'})
                    continue

                self.exec_func(json.loads(mes))

            except cryption_tools.NotEncryptedError:
                self.send({'Error': 'NotEncryptedError'})
                return

    def send(self, message: dict | list, message_type: str | None = 'function') -> None:
        message['type'] = message_type
        stringMes = json.dumps(message)

        mes = cryption_tools.MesCryp.encrypt(stringMes, key=self.key.encode())
        length = pack('>Q', len(mes))   # get message length

        self.client.sendall(length)
        self.client.sendall(mes)

    def exec_func(self, message: dict):
        """
        execute functions for the client
        """
        if message["type"] == "secReq":
            msg = {
                "content": {"sec": self.sec},
                "time": message["time"]
            }
            self.send(msg)
            return
        else:
            print(f"function '{message['type']}' type:{type(message['type'])} != 'secReq' type: str")
            error, info = self.manager.exec(message, self)
        if error:
            self.send({"Error": error, "info": info}, message_type='Error')

    def end(self) -> None:
        self.disconnect = True
        self.loop = False
        self.client.close()

    def __getitem__(self, item) -> str:
        return dict(self)[item]

    def __iter__(self) -> typing.Iterator:
        for key, item in (('key', self.key), ('name', self.name), ('sec', self.sec)):
            yield key, item

    def __repr__(self) -> str:
        return f"<class User (name: {self.name}, sec: {self.sec}, key: {self.key})>"

    def __contains__(self, item) -> bool:
        return item in self.name or item in self.key


class UserList:
    def __init__(self, users: typing.List[User] | None = ...) -> None:
        """
        initialize a list for all users and start garbage-collector

        special: ´´get_user´´ function (gets a user by its name or encryption key)
        """
        self.users = users if users is not ... else list()
        self.client_threads = list()

        self.executor = ThreadPoolExecutor()
        self.collector = self.executor.submit(self._garbage_collector, .5)

        self.loop = True

    def names(self) -> typing.Generator:
        """
        return the names of all users
        """
        for element in self.users:
            yield element.name

    def keys(self) -> typing.Generator:
        """
        return the encryption keys of all users
        """
        for element in self.users:
            yield element.key

    def append(self, obj: User) -> None:
        """
        append object to the end of the list and start receive thread
        """
        if self.__contains__(obj.name):
            self.remove_by(name=obj.name)

        self.client_threads.append(self.executor.submit(obj.receive))
        self.users.append(obj)

    def get_user(self, key: str | None = ..., name: str | None = ...) -> User:
        """
        get a user by its name or encryption key
        """
        for element in self.users:
            if key is not ...:
                if key in element:
                    return element

            if name is not ...:
                if name in element:
                    return element
        raise KeyError(f'No User with encryption key {key} or name {name} found!')

    def remove(self, user: User) -> None:
        """
        remove a user by its class
        """
        user.end()
        self.users.remove(user)

    def remove_by(self, *args, **kw) -> None:
        """
        remove a user by its username or encryption key

        arguments are the same as for UserList.get_user
        """
        self.remove(self.get_user(*args, **kw))

    def reset(self) -> None:
        """
        reset all users (clear self.users)
        """
        for user in self.users:
            user.send({'warning': 'server_logout'}, message_type="disconnect")
            user.end()
        self.users = list()

    def _garbage_collector(self, time_between_loops: int | None = .5) -> None:
        """
        check if any of the clients is disconnected and if yes, remove it
        """
        while self.loop:
            for element in self.users:
                if element.disconnect:
                    element.end()
                    self.users.remove(element)
            time.sleep(time_between_loops)

    def end(self) -> None:
        """
        shutdown all threads
        """
        self.loop = False
        for user in self.users:
            user.end()
        self.executor.shutdown(wait=False)

    def __iter__(self) -> typing.Iterator:
        for element in self.users:
            yield element

    def __contains__(self, other: str) -> bool:
        with contextlib.suppress(KeyError):
            self.get_user(name=other)
            return True

        with contextlib.suppress(KeyError):
            self.get_user(key=other)
            return True
        return False
