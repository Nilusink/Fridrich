from json import load, dump
from contextlib import suppress

# local imports
from modules.cryption_tools import low

# TemperatureReader import
import RPi.GPIO as GPIO
import dht11

# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

# read data using pin 18
instance = dht11.DHT11(pin = 18)

def readTemp():
    try:
        result = instance.read()    # happens, don't know why
    except RuntimeError:
        return None, None

    for _ in range(10): # to get a more pecice value, measure 10 times
        with suppress(AttributeError):
            tmp1 = list()
            tmp2 = list()
            invalids = int()

            while not result.is_valid():    # only if result is valid
                invalids+=1
                with suppress(RuntimeError):
                    result = instance.read()
                
                if invalids>50: # if the value of the sensor is None for 50 times
                    break
            
            if result.temperature: tmp1.append(result.temperature)  # only append values
            if result.humidity:    tmp2.append(result.humidity) # only append values

    if len(tmp1) == 0 or len(tmp2) == 0:    # if either of the list has zero elements, return error
        print('Failed to read sensor')
        return None, None

    temp = round(sum(tmp1)/len(tmp1), 2)    # get average
    hum  = round(sum(tmp2)/len(tmp2), 2)

    return temp, hum

class VOTES:    # class for votes "variable"
    def __init__(self, getFile, *args): # spciefie main file and other files to update
        self.getFile = getFile
        self.FilesToWrite = args
    
    def get(self):  # get variable from main file
        odict = load(open(self.getFile, 'r'))
        return odict
    
    def write(self, newValue:dict): # write variable to all files
        dump(newValue, open(self.getFile, 'w'), indent=4)

        for element in self.FilesToWrite:
            dump(newValue, open(element, 'w'), indent=4)
 
class Debug:
    def __init__(self, debFile):
        self.file = debFile
    
    def debug(self, *args):
        print(*args)
        with open(self.file, 'a') as out:
            for element in args:
                print(f'Wrote to file {self.file}: ', element)
                out.write(str(element)+'\n')  

def checkif(s:str, d:dict): # if s is already voted, return False, else True
    keys = [d[key] for key in d]+['Lukas', 'Melvin', 'Niclas']  # keys is (ex.) ['Fridrich', 'Lukas', 'Melvin', 'Niclas]
    for element in keys:
        if s.lower().replace(' ', '') == element.lower().replace(' ', ''):
            return element
    return s

def KeyValue(dictionary:dict):   # funktion to return a list from the Values (funktion becuz of changes)
    return list(dictionary)

def inverseDict(dictionary:dict):
    x = dict()
    for element in dictionary:
        x[dictionary[element]] = element
    return x

def getNewones(flag, VoteInstance, lastFile):   # get all attendants wich are not in the default name list
    newones = list()
    if flag=='now':
        tmp = VoteInstance.get()
    elif flag=='last':
        tmp = load(open(lastFile, 'r'))
    
    for element in tmp:
        if not tmp[element] in ['Lukas', 'Niclas', 'Melvin']+newones:
            newones.append(tmp[element])
    
    return newones

class Constants:
    def __init__(self):
        self.port = 12345
        self.ip = '0.0.0.0'
        self.Terminate = False

        direc = '/home/pi/Server/data/'
        vardirec = '/var/www/html/'

        # server files
        self.lastFile = direc+'yes.json'
        self.nowFile = direc+'now.json'
        self.KingFile = direc+'KingLog.json'
        self.CalFile = direc+'Calendar.json'
        self.crypFile = direc+'users.enc'
        self.versFile = direc+'Version'
        self.tempLog = direc+'tempData.json'
        self.doubFile = direc+'dVotes.json'
        self.logFile = direc+'Server.log'

        # web serveer files
        self.varTempLog = vardirec+'json/tempData.json'
        self.varKingLogFile = vardirec+'KingLog.log'
        self.varLogFile = vardirec+'json/KingLog.json'
        self.varNowFile = vardirec+'json/now.json'

        # fan controller files
        self.logFile = direc+'temp.log'
        self.errFile = direc+'temp.err.log'
        self.tempFile = direc+'tempData.json'

        self.String = 'abcdefghijklmnopqrstuvwxyz'                               # string for creating auth Keys
        self.String += self.String.upper()+'1234567890ß´^°!"§$%&/()=?`+*#.:,;µ@€<>|'

        self.defUser = {
            'Name':'Hurensohn', 
            'pwd':'Hurensohn'
        }