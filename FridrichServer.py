#! /usr/bin/python3
from gpiozero import CPUTemperature
import datetime, socket, time, json
from traceback import format_exc
from contextlib import suppress
from threading import Thread
from random import sample
import sys

# TemperatureReader import
import RPi.GPIO as GPIO
import dht11

# local imports
from cryption_tools import low

# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

class VOTES:
    def __init__(self, getFile, *args):
        self.getFile = getFile
        self.FilesToWrite = args
    
    def get(self):
        odict = json.load(open(self.getFile, 'r'))
        return odict
    
    def write(self, newValue:dict):
        json.dump(newValue, open(self.getFile, 'w'), indent=4)

        for element in self.FilesToWrite:
            json.dump(newValue, open(element, 'w'), indent=4)

class DoubleVote:
    globals()
    def __init__(self, filePath):
        global validUsers
        self.filePath = filePath

        try:
            value = json.load(open(self.filePath, 'r'))

        except FileNotFoundError:
            value = dict()
            for element in validUsers:
                value[element['Name']] = 1
        
        json.dump(value, open(self.filePath, 'w'))
    
    def read(self):
        return json.load(open(self.filePath, 'r'))
    
    def write(self, value:dict):
        print('updating Write')
        json.dump(value, open(self.filePath, 'w'))

    def vote(self, vote, User):
        print('called double vote')
        global Vote

        votes = Vote.get()
        value = self.read()
        if value[User] < 1:
            return False
        
        votes[User+'2'] = vote
        Vote.write(votes)

        print('set votes:', Vote.get())

        value[User] -= 1
        self.write(value)
        return True

    def unVote(self, User):
        global Vote

        votes = Vote.get()
        with suppress(NameError):
            votes.pop(User+'2')
        
        value = self.read()
        if User in value:
            value[User]+=1
        
        self.write(value)

        Vote.write(votes)
    
    def getFrees(self, User):
        value = self.read()
        if User in value:
            return value[User]
        
        self.write(value)
        return False

def getNewones(flag):   # get all attendants wich are not in the default name list
    global Vote
    newones = list()
    if flag=='now':
        tmp = Vote.get()
    elif flag=='last':
        tmp = json.load(open(lastFile, 'r'))
    
    for element in tmp:
        if not tmp[element] in ['Lukas', 'Niclas', 'Melvin']+newones:
            newones.append(tmp[element])
    
    return newones

def checkif(s:str, d:dict): # if s is already voted, return False, else True
    keys = [d[key] for key in d]+['Lukas', 'Melvin', 'Niclas']  # keys is (ex.) ['Fridrich', 'Lukas', 'Melvin', 'Niclas]
    for element in keys:
        if s.lower().replace(' ', '') == element.lower().replace(' ', ''):
            return element
    return s

def KeyFunc(length=10): # generate random key
    global String, ClientKeys
    s = ''.join(sample(String, length)) # try #1
    while s in ClientKeys: 
        s = ''.join(sample(String), length) # if try #1 is already in ClientKeys, try again
    return s

def KeyValue(dictionary:dict):   # funktion to return a list from the Values (funktion becuz of changes)
    return list(dictionary)

def inverseDict(dictionary:dict):
    x = dict()
    for element in dictionary:
        x[dictionary[element]] = element
    return x

def debug(*args):
    print(*args)
    with open(logFile, 'a') as out:
        for element in args:
            out.write(str(element)+'\n')  

def readTemp():
    result = instance.read()
    invalids = int()
    while not result.is_valid():
        invalids+=1
        result = instance.read()

        if invalids==50:
            print('failed to read sensor')
            return None, None
    
    return result.temperature, result.humidity

class ClientFuncs:  # class for the Switch
    globals()
    def vote(message, client, *args):
        global nowFile, Vote, ClientKeys
        votes = Vote.get()    # update votes
        resp = checkif(message['vote'], votes)
        name = ClientKeys[message['AuthKey']]
        votes[name] = resp    # set <hostname of client> to clients vote
        debug(f'got vote: {message["vote"]}                     .')   # print that it recievd vote (debugging)
        Vote.write(votes)  # write to file

        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))
    
    def unvote(message, client, *args):
        global nowFile, Vote
        votes = Vote.get()    # update votes
        name = ClientKeys[message['AuthKey']]
        with suppress(KeyError): 
            del votes[name]  # try to remove vote from client, if client hasn't voted yet, ignore it
        Vote.write(votes) # update file

        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))
    
    def CalendarHandler(message, client, *args):
        global CalFile
        cal = json.load(open(CalFile, 'r'))
        if not message['event'] in cal[message['date']]:    # if event is not there yet, create it
            try:
                cal[message['date']].append(message['event'])
            except (KeyError, AttributeError):
                cal[message['date']] = [message['event']]

            json.dump(cal, open(CalFile, 'w'))  # update fil
            debug(f'got Calender: {message["date"]} - "{message["event"]}"')    # notify that threr has been a calendar entry
        
        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))

    def reqHandler(message, client, *args):
        global reqCounter, nowFile
        reqCounter+=1
        if message['reqType']=='now':   # now is for the current "votes" dictionary
            with open(nowFile, 'r') as inp:
                client.send(inp.read().encode('utf-8'))

        elif message['reqType'] == 'last':  # last is for the "votes" dictionary of the last day
            with open(lastFile, 'r') as inp:
                client.send(inp.read().encode('utf-8'))
                
        elif message['reqType'] == 'log':   # returns the log of the GayKings
            with open(KingFile, 'r') as inp:
                client.send(inp.read().encode('utf-8'))
                
        elif message['reqType'] == 'attds': # returns All attendants (also non standart users)
            newones = getNewones(message['atype'])  

            client.send(json.dumps({'Names':['Lukas', 'Niclas', 'Melvin']+newones}).encode('utf-8'))    # return stardart users + new ones
                
        elif message['reqType'] == 'temps': # returns the temperatures
            rtemp, rhum = readTemp()
            client.send(json.dumps({'Room':rtemp, 'CPU':currTemp, 'Hum':rhum}).encode('utf-8'))
                
        elif message['reqType'] == 'cal':   # returns the calendar dictionary
            client.send(open(CalFile, 'r').read().encode('utf-8'))
                
        else:   # notify if an invalid request has been sent
            debug(f'Invalid Request {message["reqType"]}')

    def changePwd(message, client,  *args):
        global validUsers, ClientKeys
        name = ClientKeys[message['AuthKey']]
        for element in validUsers:
            if element['Name'] == name:
                element['pwd'] = message['newPwd']
        
        with open(crypFile, 'w') as out:
            fstring = json.dumps(validUsers)
            cstring = low.encrypt(fstring)
            out.write(cstring)
        
        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))

    def getVote(message, client, *args):
        votes = Vote.get()
        name = ClientKeys[message['AuthKey']]
        if not name in Vote.get():
            client.send(json.dumps({'Error':'NotVoted'}).encode('utf-8'))
            return
        cVote = votes[name]
        client.send(json.dumps({'Vote':cVote}).encode('utf-8'))

    def getVersion(mesage, client, *args):
        vers = open(versFile, 'r').read()
        client.send(json.dumps({'Version':vers}).encode('utf-8'))

    def setVersion(message, client, *args):
        with open(versFile, 'w') as out:
            out.write(message['version'])

        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))

    def DoubVote(message, client, *args):
        global DV, Vote
        name = ClientKeys[message['AuthKey']]
        resp = checkif(message['vote'], Vote.get())     
        resp = DV.vote(resp, name)
        if resp:
            client.send(json.dumps({'Success':'Done'}).encode('utf-8'))
        else:
            client.send(json.dumps({'Error':'NoVotes'}).encode('utf-8'))
    
    def DoubUnVote(message, client, *args):
        global DV
        name = ClientKeys[message['AuthKey']]
        DV.unVote(name)
        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))
    
    def getFreeVotes(message, client, *args):
        global DV
        name = ClientKeys[message['AuthKey']]
        frees = DV.getFrees(name)

        if frees == False:
            client.send(json.dumps({'Error':'RegistryError'}))

    def end(message, client, *args):
        global ClientKeys
        ClientKeys.pop(message['AuthKey'])

        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))

def recieve():  # Basicly the whole server
    global CalFile, server, reqCounter, ValidUsers, ClientKeys
    while not Terminate:
        try:
            # Accept Connection
            try:
                client, address = server.accept()
                del address
                #debug(f'Connected to {address}')
            except OSError:
                break
            # try to load the message, else ignore it and restart
            try:
                mes = json.loads(client.recv(1024).decode('utf-8'))
            except:
                debug('json error')
                client.close()
                continue    # if message is invalid or an other error occured, ignore the message and jump to start
            #debug(f'Got message: {mes}')

            switch = {                                  # instead of 5 billion if'S
                'vote':ClientFuncs.vote, 
                'unvote':ClientFuncs.unvote, 
                'CalEntry':ClientFuncs.CalendarHandler, 
                'req':ClientFuncs.reqHandler,
                'end':ClientFuncs.end,
                'changePwd':ClientFuncs.changePwd,
                'getVote':ClientFuncs.getVote,
                'getVersion':ClientFuncs.getVersion,
                'setVersion':ClientFuncs.setVersion,
                'dvote':ClientFuncs.DoubVote,
                'dUvote':ClientFuncs.DoubUnVote,
                'getFrees':ClientFuncs.getFreeVotes
            }

            gSwitch = {                                  # instead of 5 billion if'S
                'CalEntry':ClientFuncs.CalendarHandler, 
                'req':ClientFuncs.reqHandler,
                'end':ClientFuncs.end,
            }

            if mes['type'] == 'auth':   # authorization function
                IsValid = False
                key = None
                for element in validUsers:  # if username and password is Correct (in list)
                    if mes['Name'] == element['Name'] and mes['pwd'] == element['pwd']:
                        IsValid = True  # set to True
                        iDict = inverseDict(ClientKeys) # inversed dict
                        key = KeyFunc(length=20)    # create unique Authorization key (so this function doesn't need to be executed every time)
                        ClientKeys[key] = mes['Name']  # append key to valid keys

                    elif mes['Name'] == defUser['Name'] and mes['pwd'] == defUser['pwd']:
                        IsValid = True
                        key = KeyFunc(length=20)
                        GuestKeys.append(key)

                debug(f'Username : {mes["Name"]}, Auth: {IsValid}       ')
                client.send(json.dumps({'Auth':IsValid, 'AuthKey':key}).encode('utf-8'))    # send result to client

            else:
                if not 'AuthKey' in mes:    # if no AuthKey in message
                    debug('auth error, Key not in message')
                    client.send(json.dumps({'Error':'AuthError'}).encode('utf-8'))
                    client.close()
                    continue

                if mes['AuthKey'] in KeyValue(ClientKeys):    # if AuthKey is correct, go along
                    if mes['type'] in switch:
                        switch[mes['type']](mes, client)

                    else:
                        debug(f'Invalid Type {mes["type"]}                  ')
                        debug(mes)
                
                elif mes['AuthKey'] in KeyValue(GuestKeys):
                    if mes['type'] in gSwitch:
                        switch[mes['type']](mes, client)
                    
                    else:
                        if mes['type'] in switch:
                            debug('Access denied to guest user')
                            client.send(json.dumps({'Error':'AccessError'}).encode('utf-8'))

                        else:
                            debug(f'Invalid Type{mes["tpe"]}')
                            debug(mes)
                
                else:   # wrong AuthKey
                    client.send(json.dumps({'Error':'AuthError'}).encode('utf-8'))
                
            client.close()  # close so it can be reused

        except Exception:
            client.send(json.dumps({'Error':'Unknown'}).encode('utf-8'))
            client.close()
            debug('Thread 1 error:')
            debug(format_exc())

    server.close()

def update():   # updates every few seconds
    global currTemp, reqCounter, Vote, tempLog

    t = time.time   # time instance (for comfort)
    start = t()
    while not Terminate:

        # -------- Requests Counter ---------
        if t()-start>=1:    # every 2 seconds
            start+=1
            #s = str(reqCounter)
            #debug(' Requests in last 2 seconds: '+'0'*(3-len(s))+s, end='\r')
            reqCounter = 0
            currTemp = cpu.temperature
            roomTemp, roomHum = readTemp()
            for element in (tempLog, varTempLog):
                with open(element, 'w') as out:
                    json.dump({"temp":roomTemp, "cptemp":currTemp, "hum":roomHum}, out)
            time.sleep(.8)
        
        # --------  00:00 switch ---------
        if time.strftime('%H:%M') == '00:00':
            with open(lastFile, 'w') as out:    # get newest version of the "votes" dict and write it to the lastFile
                with open(nowFile, 'r') as inp:
                    last = inp.read()
                    out.write(last)
            
            votes = dict()  # reset votes in file and the variable
            Vote.write({})
            
            last = json.loads(last) # get last ones

            votes1 = int()
            attds = dict()
            for element in last:    # create a dict with all names and a corresponding value of 0
                attds[last[element]] = 0

            for element in last:    # if name has been voted, add a 1 to its sum
                votes1+=1
                attds[last[element]]+=1

            
            Highest = str()
            HighestInt = int()
            for element in attds:   # gets the highest of the recently created dict
                if attds[element]>HighestInt:
                    HighestInt = attds[element]
                    Highest = element

                elif attds[element]==HighestInt:
                    Highest += '|'+element
            
            if HighestInt!=0:
                kIn = json.loads(open(KingFile, 'r').read())    # write everything to logs
                kIn[time.strftime('%d.%m.%Y')] = Highest
                with open(KingFile, 'w') as out:
                    json.dump(kIn, out, indent=4)
                
                with open(varLogFile, 'w') as out:
                    json.dump(kIn, out, indent=4)
                
                with open(varKingLogFile, 'w') as out:
                    out.write(Highest)
                
                debug(f"backed up files and logged the GayKing ({time.strftime('%H:%M')})\nGaymaster: {Highest}")
            
            else:
                debug('no votes recieved')
            time.sleep(61)

############################################################################
#                              Main Program                                #
############################################################################
if __name__=='__main__':
    reqCounter = 0
    cpu = CPUTemperature()
    currTemp =cpu.temperature

    String = 'abcdefghijklmnopqrstuvwxyz'                               # string for creating auth Keys
    String += String.upper()+'1234567890ß´^°!"§$%&/()=?`+*#.:,;µ@€<>|'

    defUser = {
        'Name':'Hurensohn', 
        'pwd':'Hurensohn'
        }

    ClientKeys = dict() # list for Client AuthKeys
    GuestKeys = list()

    port = 12345
    ip = '0.0.0.0'
    Terminate = False

    direc = '/home/pi/Server/'
    vardirec = '/var/www/html/'

    lastFile = direc+'yes.json'
    nowFile = direc+'now.json'
    KingFile = direc+'KingLog.json'
    CalFile = direc+'Calendar.json'
    crypFile = direc+'users.enc'
    versFile = direc+'Version'
    tempLog = direc+'tempData.json'

    varTempLog = vardirec+'json/tempData.json'
    varKingLogFile = vardirec+'KingLog.log'
    varLogFile = vardirec+'json/KingLog.json'

    varNowFile = vardirec+'json/now.json'

    logFile = direc+'Server.log'

    doubFile = direc+'dVotes.json'

    with open(logFile, 'w') as out:
        out.write('')

    with open(crypFile, 'r') as inp:
        cstring = inp.read()
        fstring = low.decrypt(cstring)
        validUsers = json.loads(fstring)
        #debug(validUsers)  # prints all users and passwords, not recommendet!

    dayRange = 30
    try:
        cal = json.load(open(CalFile, 'r'))
        cal = dict()
        tod = datetime.datetime.now()
        for i in range(dayRange, 0, -1):
            d = datetime.timedelta(days = i)
            a = tod - d
            dForm = f'{a.day}.{a.month}.{a.year}'
            try:
                cal[dForm]
            except:
                cal[dForm] = list()
        json.dump(cal, open(CalFile, 'w'))

    except:
        cal = dict()
        tod = datetime.datetime.now()
        for i in range(dayRange, 0, -1):
            d = datetime.timedelta(days = i)
            a = tod - d
            dForm = f'{a.day}.{a.month}.{a.year}'
            cal[dForm] = list()
        json.dump(cal, open(CalFile, 'w'))

    # read data using pin 18
    instance = dht11.DHT11(pin = 18)

    Vote = VOTES(nowFile, varNowFile)
    DV   = DoubleVote(doubFile)

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((ip, port))
        server.listen()
        debug(ip)

        #ServerRecv = Thread(target=recieve, daemon=True)
        Updater    = Thread(target=update, daemon=True)

        #ServerRecv.start()
        Updater.start()
        
        recieve()	
        #ServerRecv.join()

    except:
        server.shutdown(socket.SHUT_RDWR)
        debug(format_exc())
        Terminate=True
        sys.exit(0)
