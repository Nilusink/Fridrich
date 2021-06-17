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

def getNewones(flag):   # get all attendants wich are not in the default name list
    global votes
    newones = list()
    if flag=='now':
        tmp = votes
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

        if invalids==10:
            return None, None
    
    return result.temperature, result.humidity

class ClientFuncs:  # class for the Switch
    globals()
    def vote(message, client, *args):
        global nowFile, votes, ClientKeys
        votes = json.load(open(nowFile))    # update votes
        resp = checkif(message['vote'], votes)
        name = ClientKeys[message['AuthKey']]
        votes[name] = resp    # set <hostname of client> to clients vote
        debug(f'got vote: {message["vote"]}                     .')   # print that it recievd vote (debugging)
        json.dump(votes, open(nowFile, 'w'), indent=4)  # write to file

        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))
    
    def unvote(message, client, *args):
        global nowFile, votes
        votes = json.load(open(nowFile))    # update votes
        name = ClientKeys[message['AuthKey']]
        with suppress(KeyError): 
            del votes[name]  # try to remove vote from client, if client hasn't voted yet, ignore it
        json.dump(votes, open(nowFile, 'w'), indent=4) # update file

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
        name = ClientKeys[message['AuthKey']]
        if not name in votes:
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

    def end(message, client, *args):
        global ClientKeys
        ClientKeys.pop(message['AuthKey'])

        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))

def recieve():  # Basicly the whole server
    global votes, CalFile, server, reqCounter, ValidUsers, ClientKeys
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
                'setVersion':ClientFuncs.setVersion
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
                if not 'AuthKey' in mes:    # if no authkey in message
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
                
                else:   # wrong authkey
                    client.send(json.dumps({'Error':'AuthError'}).encode('utf-8'))
                
            client.close()  # close so it can be reused

        except Exception:
            debug('Thread 1 error:')
            debug(format_exc())

    server.close()

def update():   # updates every few seconds
    global currTemp, reqCounter, votes, tempLog

    t = time.time   # time instance (for comfort)
    start = t()
    while not Terminate:

        # -------- Requests Counter ---------
        if t()-start>=2:    # every 2 seconds
            start+=2
            #s = str(reqCounter)
            #debug(' Requests in last 2 seconds: '+'0'*(3-len(s))+s, end='\r')
            reqCounter = 0
            currTemp = cpu.temperature
            roomTemp, roomHum = readTemp()
            with open(tempLog, 'w') as out:
                json.dump({"temp":roomTemp, "cptemp":currTemp, "hum":roomHum}, out)
                print('wrote to file '+tempLog)
            time.sleep(1)
        
        # --------  00:00 switch ---------
        if time.strftime('%H:%M') in ('00:00'):
            with open(lastFile, 'w') as out:    # get newest version of the "votes" dict and write it to the lastFile
                with open(nowFile, 'r') as inp:
                    last = inp.read()
                    out.write(last)
            
            votes = dict()  # reset votes in file and the variable
            with open(nowFile, 'w') as out:
                out.write('{}')
            
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

    tempLog = vardirec+'json/tempData.json'

    logFile = direc+'Server.log'

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

    try:
        votes = json.load(open(nowFile, 'r'))
    except Exception:
        votes = dict()

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
