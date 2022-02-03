"""
server sub-module
Contains all the modules that only the server needs

Author: Nilusink
"""
from dataclasses import dataclass
from typing import Dict
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
            self.dic = json.load(open(os.getcwd() + '/fridrich/server/settings.json', 'r'))

        except FileNotFoundError:
            self.dic = json.load(open('/home/apps/Fridrich/fridrich/server/settings.json', 'r'))

        for Index, Value in self.dic.items():
            setattr(self, Index, Value)

    def __getitem__(self, item) -> str | int | bool:
        return self.dic[item]


Const = Constants()


# user configuration
try:
    USER_CONFIG = json.load(open(os.getcwd() + '/fridrich/server/user_config.json', 'r'))

except FileNotFoundError:
    USER_CONFIG = json.load(open('/home/apps/Fridrich/fridrich/server/user_config.json', 'r'))
