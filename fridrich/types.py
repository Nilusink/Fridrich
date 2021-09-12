from typing import Any, Iterator
import json

class fileVar:
    def __init__(self, value : str | dict, fileS = str | list | tuple) -> None:
        "create a variable synced to one or more files"
        self.files = fileS if type(fileS) in (list, tuple) else [fileS]

        self.set(value) # assign variable

    def __repr__(self) -> str:
        return repr(self.value)

    def __len__(self) -> int:
        "return the lenght of ``self.value``"
        return len(self.value)

    def __str__(self) -> str:
        "return string of ``self.value``"
        self.get()
        return str(self.value)

    # str options
    def __add__(self, other : str) -> str:
        self.get()
        self.checktype(str)

        self.set(self.value+other)

    # dict options
    def __getitem__(self, key:str) -> Any:
        "get an item if ``self.value`` is a dict"
        self.get() # update variable in case something in the file has changed
        self.checktype(dict)
        if not key in self.value:
            raise KeyError(f'"{key}" not in dict "{self.value}"')
        return self.value[key]

    def __setitem__(self, key, value) -> dict:
        "set an item of a dict"
        self.get()
        self.checktype(dict)

        self.value[key] = value
        self.set(self.value)

        return self.value

    def __delitem__(self, key: str) -> None:
        self.get()
        self.checktype(dict)

        del self.value[key]

    def __iter__(self) -> Iterator:
        self.get()
        self.checktype(dict)

        for key, item in self.value.items():
            yield key, item

    # general options
    def __eq__(self, other) -> bool:
        "check if the ``==`` given value is the same as either the whole class or the value"
        self.get()
        if type(other) == fileVar:
            return other.value == self.value and list(other.files) == list(self.files)

        return other == self.value

    def __contains__(self, other) -> bool:
        self.get()
        return other in self.value

    def set(self, value : str | dict) -> None:
        "set the variable (update files)"
        self.value = value
        self.type = type(value)

        for file in self.files:
            with open(file, 'w') as out:
                if self.type == dict:
                    json.dump(self.value, out, indent=4)
                    print(f'wrote {value} to file: {file}')
                    continue
                out.write(self.value)

    def get(self) -> str | dict:
        "get the variable in its original type"
        file = self.files[0]
        with open(file, 'r') as inp:
            try:
                self.value =  json.load(inp)

            except json.JSONDecodeError: 
                self.value = inp.read()
        
        self.type = type(self.value)

        return self.value

    def checktype(self, wantedtype : str | dict) -> None:
        "if type is wrong, raise an error"
        if not self.type == wantedtype:
            raise TypeError(f'Expected {wantedtype}, got {self.type}. This function is not available for the given variabletype')
