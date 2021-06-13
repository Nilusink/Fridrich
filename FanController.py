from gpiozero import CPUTemperature, LED
import time

def CPUHeatHandler():
    global currTemp

    cpu = CPUTemperature()
    Trigger = False
    tv = True
    triggmap = {True:On.on, False:On.off}
    tvmap    = {True:TV.on, False:TV.off}
    while True:
        currTemp = cpu.temperature
        if currTemp>50:
            with open(errFile, 'w') as out:
                out.write(f'CPU temp: {currTemp} - {time.strftime("%H:%M")} | Fan: {Trigger}, 3.3V: {tv}')
            from os import system
            system('sudo shutdown now')

        elif currTemp>35:
            Trigger = True
            tv = False

        elif currTemp and not Trigger:
            Trigger = True
            tv = True
        
        elif currTemp<30:
            tv = True
        
        elif currTemp<25 and Trigger:
            Trigger = False
            tv = True
        
        triggmap[Trigger]()
        tvmap[tv]()
        
        print(' CPU temp: ', currTemp, time.strftime('%H:%M'), ' | Fan: ', Trigger, ' 3.3V: ', tv, end='\r')
        with open(logFile, 'w') as out:
            out.write(f'CPU temp: {currTemp} - {time.strftime("%H:%M")} | Fan: {Trigger}, 3.3V: {tv}')        
        time.sleep(10)

if __name__=='__main__':
    logFile = '/home/pi/Server/temp.log'
    errFile = '/home/pi/Server/temp.err.log'

    TV = LED(20)
    On = LED(21)

    CPUHeatHandler()