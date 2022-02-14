"""
helper classes used by server and backend

Author:
Nilusink
"""
import typing
import json
import time


class Daytime:
    """
    class for calculating with HH:MM:SS
    """
    def __init__(self, hour: int = 0, minute: int = 0, second: int = 0) -> None:
        self.hour = hour
        self.minute = minute
        self.second = second

    @property
    def hour(self) -> int:
        return self.__hour

    @hour.setter
    def hour(self, value: int) -> None:
        self.__hour = value % 24
        while self.__hour < 0:
            self.__hour += 24

    @property
    def minute(self) -> int:
        return self.__minute

    @minute.setter
    def minute(self, value: int) -> None:
        self.__minute = value % 60
        while self.__minute < 0:
            self.__minute += 60

    @property
    def second(self) -> int:
        return self.__second

    @second.setter
    def second(self, value: int) -> None:
        self.__second = value % 60
        while self.__second < 0:
            self.__second += 60

    @staticmethod
    def from_abs(absolute_value: int) -> "Daytime":
        """
        convert an absolute value (seconds) to a Daytime

        :param absolute_value: the absolute time value in seconds
        """
        if type(absolute_value) != int:
            raise ValueError("only accepts of type int")

        # making sure the value is in range of the 24 hour time format
        while absolute_value < 0:
            absolute_value += 24*3600

        while absolute_value > 24*3600:
            absolute_value -= 24*3600

        # splitting up in Hour, Minute, Second
        hour = absolute_value // 3600
        absolute_value -= hour * 3600
        minute = absolute_value // 60
        absolute_value -= minute * 60
        return Daytime(hour=hour, minute=minute, second=absolute_value)

    @staticmethod
    def from_strftime(string_time: str, sep: str = ":") -> "Daytime":
        """
        from format "HH:MM:SS"
        """
        parts = string_time.split(sep)
        parts += ["00"] * (3-len(parts))
        return Daytime(hour=int(parts[0]), minute=int(parts[1]), second=int(parts[2]))

    @staticmethod
    def now() -> "Daytime":
        """
        Daytime object with current time
        """
        return Daytime(hour=int(time.strftime("%H")), minute=int(time.strftime("%M")), second=int(time.strftime("%S")))

    # mathematics
    def __add__(self, other: "Daytime") -> "Daytime":
        return Daytime.from_abs(abs(self) + abs(other))

    def __iadd__(self, other: "Daytime") -> "Daytime":
        self.__dict__ = self.__add__(other).__dict__
        return self

    def __sub__(self, other: "Daytime") -> "Daytime":
        return Daytime.from_abs(abs(self) - abs(other))

    def __isub__(self, other: "Daytime") -> "Daytime":
        self.__dict__ = self.__sub__(other).__dict__
        return self

    # comparison
    def __eq__(self, other: "Daytime") -> bool:
        return abs(self) == abs(other)

    def __ne__(self, other: "Daytime") -> bool:
        return abs(self) != abs(other)

    def __lt__(self, other: "Daytime") -> bool:
        return abs(self) < abs(other)

    def __le__(self, other: "Daytime") -> bool:
        return abs(self) <= abs(other)

    def __gt__(self, other: "Daytime") -> bool:
        return abs(self) > abs(other)

    def __ge__(self, other: "Daytime") -> bool:
        return abs(self) >= abs(other)

    # representation
    def __str__(self) -> str:
        return f"{'0' if self.hour < 10 else ''}{self.hour}:{'0' if self.minute < 10 else ''}" \
               f"{self.__minute}:{'0' if self.second < 10 else ''}{self.__second}"

    def to_string(self) -> str:
        """
        call __str__
        """
        return self.__str__()

    def __repr__(self) -> str:
        return f"<Daytime: {self.__str__()}>"

    def __bool__(self) -> bool:
        return bool(self.__abs__())

    def __abs__(self) -> int:
        """
        returns time in seconds
        """
        return self.hour * 3600 + self.minute * 60 + self.second

    # accessibility
    def __getitem__(self, item: str) -> int:
        match item:
            case "hour":
                return self.hour
            case "minute":
                return self.minute
            case "second":
                return self.second
            case _:
                raise ValueError(f"{item} is not a valid variable!")

    def __setitem__(self, item: str, value: int) -> None:
        match item:
            case "hour":
                self.hour = value
            case "minute":
                self.minute = value
            case "second":
                self.second = value
            case _:
                raise ValueError(f"{item} is not a valid variable!")

    def __delitem__(self, item: str) -> None:
        match item:
            case "hour":
                self.hour = 0
            case "minute":
                self.minute = 0
            case "second":
                self.second = 0
            case _:
                raise ValueError(f"{item} is not a valid variable!")


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
