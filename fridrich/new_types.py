import typing
import json


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
    def __init__(self, name: str, sec: str, key: str) -> None:
        """
        ´´name´´: Name of the client
        ´´sec´´: security clearance
        ´´key´´: encryption key of client
        """
        self.name = name
        self.sec = sec
        self.key = key

    def __getitem__(self, item) -> str:
        return dict(self)[item]

    def __iter__(self) -> typing.Iterator:
        for key, item in (('key', self.key), ('name', self.name), ('sec', self.sec)):
            yield key, item

    def __contains__(self, item) -> bool:
        return item in self.name or item in self.key


class UserList:
    def __init__(self, users: typing.List[User] | None = ...) -> None:
        """
        initialize a list for all users

        special: ´´get_user´´ function (gets a user by its name or encryption key)
        """
        self.users = users if users is not ... else list()

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
        append object to the end of the list
        """
        self.users.append(obj)

    def get_user(self, key: str | None = ..., name: str | None = ...) -> User:
        """
        get a user by its name or encryption key
        """
        for element in self.users:
            if key in element or name in element:
                return element
        raise KeyError(f'No User with encryption key {key} or name {name} found!')

    def remove(self, user: User) -> None:
        """
        remove a user by its class
        """
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
        self.users = list()

    def __iter__(self) -> typing.Iterator:
        for element in self.users:
            yield element
