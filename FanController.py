from gpiozero import CPUTemperature, LED
import time

def CPUHeatHandler():
    global currTemp

    cpu = CPUTemperature()
    Trigger = False
    triggmap = {True:On.on, False:On.off}
    while True:
        currTemp = cpu.temperature
        if currTemp>50:
            with open(errFile, 'w') as out:
                out.write(f'CPU temp: {currTemp} - {time.strftime("%H:%M")} | Fan: {Trigger}')
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

if __name__=='__main__':
    logFile = '/home/pi/Server/temp.log'
    errFile = '/home/pi/Server/temp.err.log'
    On = LED(21)

    CPUHeatHandler()