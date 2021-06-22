from gpiozero import CPUTemperature, LED
from traceback import format_exc
import time, json

def CPUHeatHandler():
    global currTemp
    On = LED(21)
    cpu = CPUTemperature()
    Trigger = False
    triggmap = {True:On.on, False:On.off}
    while True:
        try:
            file = json.load(open(tempFile, 'r'))
            maxtemp = file['temp']+25 if file['temp'] else 100
            currTemp = cpu.temperature
            if currTemp>maxtemp:
                with open(errFile, 'w') as out:
                    out.write(f'CPU temp: {currTemp}, Room Temperature: {file["temp"]} - {time.strftime("%H:%M")} | Fan: {Trigger}')
                from os import system
                system('sudo shutdown now')
            
            if 0<int(time.strftime('%H'))<7:
                Trigger = False
            else:
                Trigger = True
            
            triggmap[Trigger]()
            
            print(' CPU temp: ', currTemp, time.strftime('%H:%M'), ' | Fan: ', Trigger, end='\r')
            with open(logFile, 'w') as out:
                out.write(f'CPU temp: {currTemp} - {time.strftime("%H:%M")} | Fan: {Trigger}')        
            time.sleep(10)

        except:
            with open(errFile, 'a') as out:
                out.write(format_exc())
            exit()

if __name__=='__main__':
    logFile = '/home/pi/Server/temp.log'
    errFile = '/home/pi/Server/temp.err.log'

    tempFile = '/home/pi/Server/tempData.json'

    CPUHeatHandler()