from gpiozero import CPUTemperature, LED
from traceback import format_exc
import time, json

class CPUHeatHandler():
    def __init__(self):
        self.On = LED(21)
        self.cpu = CPUTemperature()
        self.Trigger = False
        self.triggmap = {True:self.On.on, False:self.On.off}
    
    def iter(self):
        try:
            file = json.load(open(tempFile, 'r'))
            maxtemp = file['temp']+25 if file['temp'] else 100
            currTemp = self.cpu.temperature
            if currTemp>maxtemp:
                with open(errFile, 'w') as out:
                    out.write(f'CPU temp: {currTemp}, Room Temperature: {file["temp"]} - {time.strftime("%H:%M")} | Fan: {self.Trigger}')
                from os import system
                system('sudo shutdown now')
            
            if 0<int(time.strftime('%H'))<7:
                Trigger = False
            else:
                Trigger = True
            
            self.triggmap[Trigger]()
            
            print(' CPU temp: ', currTemp, time.strftime('%H:%M'), ' | Fan: ', Trigger, end='\r')
            with open(logFile, 'w') as out:
                out.write(f'CPU temp: {currTemp} - {time.strftime("%H:%M")} | Fan: {Trigger}')        
            time.sleep(10)

        except:
            with open(errFile, 'a') as out:
                out.write(format_exc())
    

if __name__=='__main__':
    logFile = '/home/pi/Server/temp.log'
    errFile = '/home/pi/Server/temp.err.log'

    tempFile = '/home/pi/Server/tempData.json'

    CPUHeatHandler()