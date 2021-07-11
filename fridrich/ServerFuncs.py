from fridrich.cryption_tools import tryDecrypt
from datetime import datetime as dd
from json import load, dump, dumps
from traceback import format_exc
from contextlib import suppress
from time import strftime

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

def checkif(s:str, d:dict, voting:str): # if s is already voted, return False, else True
    if voting in d:
        d = d[voting]
        keys = [d[key] for key in d]+['Lukas', 'Melvin', 'Niclas']  # keys is (ex.) ['Fridrich', 'Lukas', 'Melvin', 'Niclas]
        print(keys)
        for element in keys:
            print(element)
            if s.lower().replace(' ', '') == element.lower().replace(' ', ''):
                return element
        return s
    return s

def KeyValue(dictionary:dict):   # funktion to return a list from the Values (funktion becuz of changes)
    return list(dictionary)

def inverseDict(dictionary:dict):
    x = dict()
    for element in dictionary:
        x[dictionary[element]] = element
    return x

def getNewones(flag, VoteInstance, lastFile, voting):   # get all attendants wich are not in the default name list
    newones = list()
    if flag=='now':
        tmp = VoteInstance.get()
    elif flag=='last':
        tmp = load(open(lastFile, 'r'))
    
    for element in tmp[voting]:
        if not tmp[element] in ['Lukas', 'Niclas', 'Melvin']+newones:
            newones.append(tmp[element])
    
    return newones

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
        with open(self.file, 'w') as out:
            out.write('')
    
    def debug(self, *args):
        print(*args)
        with open(self.file, 'a') as out:
            for element in args:
                out.write(str(element)+'\n')
    
    def catchTraceback(self):
        def wrapper(func, *args, **kw):
            try:
                func(*args, **kw)
            except:
                err = '\n\n\n'+strftime('%H:%M:%S')+'\n'+format_exc()
                print(err)
                with open(self.file, 'a') as out:
                    out.write(err)
        return wrapper

class Chat:
    def add(message, fromUser):
        mes = Chat.get()    	# get message list from file

        curr_time = dd.now()
        formatted_time = curr_time.strftime('%H:%M:%S.%f')+strftime(' - %d.%m.%Y')
        mes.append({'time':formatted_time, 'content':message, 'user':fromUser})  # append message
        dump(mes, open(con.ChatFile, 'w'), indent=4)  # write message
    
    def get():
        try:
            mes = load(open(con.ChatFile, 'r')) # try to read file
        except FileNotFoundError:
            mes = list()    # if file doesn't exist, create new list
        return mes

class Communication:
    def send(client, message:dict, encryption=None, key=None):
        stringMes = dumps(message, ensure_ascii=False)
        print(stringMes)
        if encryption:
            mes = encryption(stringMes, key=key)
            #print(mes)
            with suppress((OSError, AttributeError)):
                client.send(mes if type(mes) == bytes else mes.encode('utf-8'))
            return
        with suppress((OSError, AttributeError)):
            client.send(stringMes.encode('utf-8'))

    def recieve(server, debugingMethod, Keys):
        # Accept Connection
            try:
                client, address = server.accept()
                del address
                #debug.debug(f'Connected to {address}')
            except OSError:
                return False
            # try to load the message, else ignore it and restart
            mes = client.recv(2048)
            mes = tryDecrypt(mes, Keys)

            if not mes:
                debugingMethod('Message Error')
                with suppress(AttributeError):
                    Communication.send(client, {'Error':'MessageError', 'info':'Invalid Message/AuthKey'})
                    client.close()
                return None, None
            return client, mes

 # if message is invalid or an other error occured, ignore the message and jump to start
            
            return mes
            #debug.debug(f'Got message: {mes}')
class Constants:
    def __init__(self):
        try:
            dic = load(open('modules/constants.json', 'r'))
        except FileNotFoundError:
            dic = load(open('/home/pi/Server/fridrich/constants.json', 'r'))
        
        for Index, Value in dic.items():
            setattr(self, Index, Value)

con = Constants()