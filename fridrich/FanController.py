from fridrich import ServerFuncs
import traceback
import time
import json


# TemperatureReader import
from gpiozero import CPUTemperature, LED


class CPUHeatHandler:
    """
    handler for the cpu temperature/fan
    """
    def __init__(self) -> None:
        """
        they say with this class you could handle the cpu temperature

        but can you trust them?
        """
        self.On = LED(21)
        self.cpu = CPUTemperature()
        self.Trigger = False
        self.trigger = {True: self.On.on, False: self.On.off}
        self.const = ServerFuncs.Constants()
    
    def iter(self) -> bool | str:
        """
        new cycle
        """
        try:
            file = json.load(open(self.const.tempFile, 'r'))
            max_temp = file['temp']+25 if file['temp'] else 60
            currTemp = self.cpu.temperature
            if currTemp > max_temp:
                with open(self.const.errFile, 'w') as out:
                    out.write(f'CPU temp: {currTemp}, Room Temperature: {file["temp"]} - {time.strftime("%H:%M")} | Fan: {self.Trigger}')
                from os import system
                system('sudo shutdown now')
            
            if 0 <= int(time.strftime('%H')) < 7:
                Trigger = False
            else:
                Trigger = True
            
            self.trigger[Trigger]()
            with open(self.const.logFile, 'w') as out:
                out.write(f'CPU temp: {currTemp}, Room Temperature: {file["temp"]} - {time.strftime("%H:%M")} | Fan: {Trigger}')        
            return True

        except Exception:
            print(traceback.format_exc())
            with open(self.const.errFile, 'a') as out:
                out.write(traceback.format_exc())
            return traceback.format_exc()


if __name__ == '__main__':
    c = CPUHeatHandler()
    while True:
        c.iter()
