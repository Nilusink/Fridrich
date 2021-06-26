from gpiozero import CPUTemperature, LED
from traceback import format_exc
import time, json

from modules.ServerFuncs import Constants

class CPUHeatHandler():
    def __init__(self):
        self.On = LED(21)
        self.cpu = CPUTemperature()
        self.Trigger = False
        self.triggmap = {True:self.On.on, False:self.On.off}
        self.const = Constants()
    
    def iter(self):
        try:
            file = json.load(open(self.const.tempFile, 'r'))
            maxtemp = file['temp']+25 if file['temp'] else 100
            currTemp = self.cpu.temperature
            if currTemp>maxtemp:
                with open(self.const.errFile, 'w') as out:
                    out.write(f'CPU temp: {currTemp}, Room Temperature: {file["temp"]} - {time.strftime("%H:%M")} | Fan: {self.Trigger}')
                from os import system
                system('sudo shutdown now')
            
            if 0<int(time.strftime('%H'))<7:
                Trigger = False
            else:
                Trigger = True
            
            self.triggmap[Trigger]()
            
            print(' CPU temp: ', currTemp, time.strftime('%H:%M'), ' | Fan: ', Trigger, end='\r')
            with open(self.const.logFile, 'w') as out:
                out.write(f'CPU temp: {currTemp}, Room Temperature: {file["temp"]} - {time.strftime("%H:%M")} | Fan: {Trigger}')        
            return True

        except:
            print(format_exc())
            with open(self.const.errFile, 'a') as out:
                out.write(format_exc())
            return format_exc()

if __name__=='__main__':
    c = CPUHeatHandler()
    while True:
        c.iter()