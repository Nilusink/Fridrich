"""
server sub-module
Contains all the modules that only the server needs

Author: Nilusink
"""
import json
import os


class Constants:
    """
    All constants (modify in file settings.json)
    """

    def __init__(self) -> None:
        """
        create instance
        """
        # type hinting
        self.port: int | None = ...
        self.ip: str | None = ...
        self.Terminate: bool | None = ...

        self.direc: str | None = ...
        self.vardirec: str | None = ...

        self.lastFile: str | None = ...
        self.nowFile: str | None = ...
        self.KingFile: str | None = ...
        self.CalFile: str | None = ...
        self.crypFile: str | None = ...
        self.versFile: str | None = ...
        self.tempLog: str | None = ...
        self.doubFile: str | None = ...
        self.SerlogFile: str | None = ...
        self.SerUpLogFile: str | None = ...
        self.ChatFile: str | None = ...
        self.VarsFile: str | None = ...
        self.WeatherDir: str | None = ...

        self.varTempLog: str | None = ...
        self.varKingLogFile: str | None = ...
        self.varLogFile: str | None = ...
        self.varNowFile: str | None = ...

        self.logFile: str | None = ...
        self.errFile: str | None = ...
        self.tempFile: str | None = ...

        self.DoubleVotes: int | None = ...

        self.DoubleVoteResetDay: str | None = ...
        self.switchTime: str | None = ...
        self.rebootTime: str | None = ...
        self.status_led_pin: int | None = ...
        self.status_led_sleep_time: list | None = ...

        self.AppStoreDirectory: str | None = ...

        # get variable values
        try:
            self.dic = json.load(open(os.getcwd() + '/fridrich/server/settings.json', 'r'))

        except FileNotFoundError:
            self.dic = json.load(open('/home/pi/Server/fridrich/server/settings.json', 'r'))

        for Index, Value in self.dic.items():
            setattr(self, Index, Value)

    def __getitem__(self, item) -> str | int | bool:
        return self.dic[item]


Const = Constants()
