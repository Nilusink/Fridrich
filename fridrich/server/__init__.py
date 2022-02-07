"""
server sub-module
Contains all the modules that only the server needs

Author: Nilusink
"""
from fridrich import ConsoleColors
from dataclasses import dataclass
import traceback
import datetime
import typing
import types
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

    def catch_traceback(self, raise_error: bool = False) -> typing.Callable:
        """
        execute function with traceback and debug all errors
        """
        def decorator(func: types.FunctionType) -> typing.Callable:
            def wrapper(*args, **kw) -> None:
                try:
                    return func(*args, **kw)

                except Exception as e:
                    err = f'{ConsoleColors.FAIL}\n\n\n######## - Exception "{e}" at function {func.__name__} on {datetime.datetime.now().strftime("%H:%M:%S.%f")} -' \
                          f' ########\n\n{traceback.format_exc()}\n\n######## - END OF EXCEPTION - ########\n\n\n{ConsoleColors.ENDC}'
                    self.debug(err)
                    if raise_error:
                        raise

            return wrapper
        return decorator

    def write_traceback(self, error: type, from_user: str | None = ...) -> None:
        """
        write a caught error
        """
        err = '\n\n\n' + (
            "From User: " + from_user if from_user is not ... else "") + f'######## - Exception "{error}" on {datetime.datetime.now().strftime("%H:%M:%S.%f")} - ########\n\n{traceback.format_exc()}\n\n######## - END OF EXCEPTION - ########\n\n\n'
        self.debug(err)


Const = Constants()
DEBUGGER = Debug(Const.SerlogFile, Const.errFile)
