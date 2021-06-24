#! /usr/bin/python3
from gpiozero import CPUTemperature
import datetime, socket, time, json
from traceback import format_exc
from contextlib import suppress
from threading import Thread
from random import sample
import sys

# local imports
from modules.FanController import CPUHeatHandler
from modules.cryption_tools import low
from modules.Accounts import manager
from modules.ServerFuncs import *

class DoubleVote:
    globals()
    def __init__(self, filePath):
        validUsers = json.loads(low.decrypt(open(Const.crypFile, 'r').read()))
        self.filePath = filePath

        try:
            value = load(open(self.filePath, 'r'))

        except FileNotFoundError:
            value = dict()
            for element in validUsers:
                value[element['Name']] = 1
        
        dump(value, open(self.filePath, 'w'))
    
    def read(self):
        return load(open(self.filePath, 'r'))
    
    def write(self, value:dict):
        dump(value, open(self.filePath, 'w'))

    def vote(self, vote, User):
        global Vote

        votes = Vote.get()
        value = self.read()
        if User in value:
            if value[User] < 1:
                return False
        
            votes[User+'2'] = vote
            Vote.write(votes)

            value[User] -= 1
            self.write(value)
            return True
        
        value[User] = 0
        Vote.write(value)
        return False

    def unVote(self, User):
        global Vote

        votes = Vote.get()
        with suppress(KeyError):
            votes.pop(User+'2')
        
            value = self.read()
            value[User]+=1
            
            self.write(value)
            Vote.write(votes)
    
    def getFrees(self, User):
        value = self.read()
        print(value)
        print(f'user {User} in value: {User in value}')
        if User in value:
            return value[User]

        return False

def KeyFunc(length=10): # generate random key
    global  ClientKeys
    s = ''.join(sample(Const.String, length)) # try #1
    while s in ClientKeys: 
        s = ''.join(sample(Const.String), length) # if try #1 is already in ClientKeys, try again
    return s

def sendSuccess(client):
    client.send(json.dumps({'Success':'Done'}).encode('utf-8'))

def verify(username, password, client):
    resp = AccManager.verify(username, password)
    IsValid = False
    key = None
    if resp == None:
        client.send(json.dumps({'Error':'SecurityNotSet'}).encode('utf-8'))
        return

    elif resp:
        IsValid = True
        key = KeyFunc(length=30)
        ClientKeys[key] = resp
        
    debug.debug(f'Username : {username}, Auth: {IsValid}')
    client.send(json.dumps({'Auth':IsValid, 'AuthKey':key}).encode('utf-8'))    # send result to client

class FunctionManager:
    def __init__(self):
        self.switch = {
            'admin' : {
                'getUsers':AdminFuncs.getAccounts,
                'setPwd':AdminFuncs.setPassword,
                'setName':AdminFuncs.setUsername,
                'setSec':AdminFuncs.setSecurity,
                'newUser':AdminFuncs.addUser,
                'rmUser':AdminFuncs.rmUser,
                'end':AdminFuncs.end,

                'setVersion':ClientFuncs.setVersion,
                'getVersion':ClientFuncs.setVersion
            },
            'user' : {                                  # instead of 5 billion if'S
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
            },
            'guest' : {                                  # instead of 5 billion if'S
                'CalEntry':ClientFuncs.CalendarHandler, 
                'req':ClientFuncs.reqHandler,
                'end':ClientFuncs.end,
            }
        }
    
    def exec(self, message, client):
        clearance = ClientKeys[message['AuthKey']][0]
        if clearance in self.switch:
            if message['type'] in self.switch[clearance]:
                self.switch[clearance][message['type']](message, client)
                return False, None
            
            else:
                isIn = False
                for element in self.switch:
                    if message['type'] in self.switch[element]:
                        isIn = True
                        req  = element 
                        break
                
                if isIn:
                    return 'ClearanceIssue', f'Clrearance reqired: "{req}"'
                
                else:
                    return 'InvalidRequest', f'Invalid Request: "{message["type"]}"'

        else:
            return 'ClearanceIssue', f'Clearance not set: "{clearance}"'
        
class AdminFuncs:
    def getAccounts(message, client, *args):
        acclist = AccManager.getAccs() # getting and decrypting accounts list
        client.send(json.dumps(acclist).encode('utf-8')) # sending list to client
    
    def setPassword(message, client, *args):
        AccManager.setPwd(message['User'], message['newPwd'])   # set new password
        sendSuccess(client) # send success

    def setUsername(message, client, *args):
        AccManager.setUserN(message['OldUser'], message['NewUser']) # change account name 
        sendSuccess(client) # send success
    
    def setSecurity(message, client, *args):
        AccManager.setUserSec(message['Name'], message['sec'])
        sendSuccess(client)

    def addUser(message, client, *args):
        AccManager.newUser(message['Name'], message['pwd'], message['sec'])
        sendSuccess(client)
    
    def rmUser(message, client, *args):
        AccManager.rmUser(message['Name'])
        sendSuccess(client)

    def end(message, *args):
        with suppress(Exception):
            ClientKeys.pop(message['AuthKey'])

class ClientFuncs:  # class for the Switch
    globals()
    def vote(message, client, *args):
        global  Vote, ClientKeys
        votes = Vote.get()    # update votes
        resp = checkif(message['vote'], votes)
        name = ClientKeys[message['AuthKey']][1]
        votes[name] = resp    # set <hostname of client> to clients vote
        debug.debug(f'got vote: {message["vote"]}                     .')   # print that it recievd vote (debugging)
        Vote.write(votes)  # write to file

        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))
    
    def unvote(message, client, *args):
        global nowFile, Vote
        votes = Vote.get()    # update votes
        name = ClientKeys[message['AuthKey']][1]
        with suppress(KeyError): 
            del votes[name]  # try to remove vote from client, if client hasn't voted yet, ignore it
        Vote.write(votes) # update file

        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))
    
    def CalendarHandler(message, client, *args):
        global CalFile
        cal = json.load(open(Const.CalFile, 'r'))
        if not message['event'] in cal[message['date']]:    # if event is not there yet, create it
            try:
                cal[message['date']].append(message['event'])
            except (KeyError, AttributeError):
                cal[message['date']] = [message['event']]

            json.dump(cal, open(Const.CalFile, 'w'))  # update fil
            debug.debug(f'got Calender: {message["date"]} - "{message["event"]}"')    # notify that threr has been a calendar entry
        
        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))

    def reqHandler(message, client, *args):
        global reqCounter, nowFile, Vote, lastFile
        reqCounter+=1
        if message['reqType']=='now':   # now is for the current "votes" dictionary
            with open(Const.nowFile, 'r') as inp:
                client.send(inp.read().encode('utf-8'))

        elif message['reqType'] == 'last':  # last is for the "votes" dictionary of the last day
            with open(Const.lastFile, 'r') as inp:
                client.send(inp.read().encode('utf-8'))
                
        elif message['reqType'] == 'log':   # returns the log of the GayKings
            with open(Const.KingFile, 'r') as inp:
                client.send(inp.read().encode('utf-8'))
                
        elif message['reqType'] == 'attds': # returns All attendants (also non standart users)
            newones = getNewones(message['atype'], Vote, Const.lastFile)  

            client.send(json.dumps({'Names':['Lukas', 'Niclas', 'Melvin']+newones}).encode('utf-8'))    # return stardart users + new ones
                
        elif message['reqType'] == 'temps': # returns the temperatures
            rtemp, rhum = readTemp()
            client.send(json.dumps({'Room':rtemp, 'CPU':currTemp, 'Hum':rhum}).encode('utf-8'))
                
        elif message['reqType'] == 'cal':   # returns the calendar dictionary
            client.send(open(Const.CalFile, 'r').read().encode('utf-8'))
                
        else:   # notify if an invalid request has been sent
            debug.debug(f'Invalid Request {message["reqType"]}')

    def changePwd(message, client,  *args):
        global ClientKeys
        validUsers = json.loads(low.decrypt(open(Const.crypFile, 'r').read()))
        name = ClientKeys[message['AuthKey']][1]
        for element in validUsers:
            if element['Name'] == name:
                element['pwd'] = message['newPwd']
        
        with open(Const.crypFile, 'w') as out:
            fstring = json.dumps(validUsers)
            cstring = low.encrypt(fstring)
            out.write(cstring)
        
        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))

    def getVote(message, client, *args):
        votes = Vote.get()
        if 'flag' in message:
            x = '2' if message['flag'] == 'double' else ''
        else:
            x = ''

        name = ClientKeys[message['AuthKey']][1] + x
        if not name in Vote.get():
            client.send(json.dumps({'Error':'NotVoted'}).encode('utf-8'))
            return
        cVote = votes[name]
        client.send(json.dumps({'Vote':cVote}).encode('utf-8'))

    def getVersion(mesage, client, *args):
        vers = open(Const.versFile, 'r').read()
        client.send(json.dumps({'Version':vers}).encode('utf-8'))

    def setVersion(message, client, *args):
        with open(Const.versFile, 'w') as out:
            out.write(message['version'])

        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))

    def DoubVote(message, client, *args):
        global DV, Vote
        name = ClientKeys[message['AuthKey']][1]
        resp = checkif(message['vote'], Vote.get())     
        resp = DV.vote(resp, name)
        if resp:
            client.send(json.dumps({'Success':'Done'}).encode('utf-8'))
        else:
            client.send(json.dumps({'Error':'NoVotes'}).encode('utf-8'))
    
    def DoubUnVote(message, client, *args):
        global DV
        name = ClientKeys[message['AuthKey']][1]
        DV.unVote(name)
        client.send(json.dumps({'Success':'Done'}).encode('utf-8'))
    
    def getFreeVotes(message, client, *args):
        global DV
        name = ClientKeys[message['AuthKey']][1]
        frees = DV.getFrees(name)

        if frees == False and frees != 0:
            client.send(json.dumps({'Error':'RegistryError'}).encode('utf-8'))
            return
        client.send(json.dumps({'Value':frees}).encode('utf-8'))

    def end(message, *args):
        global ClientKeys
        with suppress(Exception):
            ClientKeys.pop(message['AuthKey'])

def recieve():  # Basicly the whole server
    global server, reqCounter, ClientKeys
    while not Const.Terminate:
        try:
            # Accept Connection
            try:
                client, address = server.accept()
                del address
                #debug.debug(f'Connected to {address}')
            except OSError:
                break
            # try to load the message, else ignore it and restart
            try:
                mes = json.loads(client.recv(1024).decode('utf-8'))
            except:
                debug.debug('json error')
                client.close()
                continue    # if message is invalid or an other error occured, ignore the message and jump to start
            #debug.debug(f'Got message: {mes}')

            if mes['type'] == 'auth':   # authorization function
                verify(mes['Name'], mes['pwd'], client)

            elif mes['type'] == 'secReq':
                client.send(json.dumps({'sec':ClientKeys[mes['AuthKey'][0]]}).encode('utf-8'))

            else:
                if not 'AuthKey' in mes:    # if no AuthKey in message
                    debug.debug('auth error, Key not in message')
                    client.send(json.dumps({'Error':'AuthError'}).encode('utf-8'))
                    client.close()
                    continue

                else:
                    try:
                        error, info = FunManager.exec(mes, client)
                        fullTraceback = None

                    except Exception as e:
                        error = str(type(e)).split("'")[1]
                        info  = str(e)
                        fullTraceback = format_exc()

                    if error:
                        if fullTraceback:
                            print(fullTraceback)
                        client.send(json.dumps({'Error':error, 'info':info, 'full':fullTraceback}).encode('utf-8'))
                
            client.close()  # close so it can be reused

        except Exception as e:
            with suppress(BrokenPipeError):
                error = str(type(e)).split("'")[1]
                info  = str(e)
                fullTraceback = format_exc()
                client.send(json.dumps({'Error':error, 'info':info, 'full':fullTraceback}).encode('utf-8'))
                client.close()

            debug.debug('Thread 1 error:')
            debug.debug(format_exc())

def update():   # updates every few seconds
    global currTemp, reqCounter, Vote, FanC

    t = time.time   # time instance (for comfort)
    start = t()
    start1 = start
    while not Const.Terminate:
        # -------- Requests Counter ---------
        if t()-start>=1:    # every 2 seconds
            start+=1
            #s = str(reqCounter)
            #debug.debug(' Requests in last 2 seconds: '+'0'*(3-len(s))+s, end='\r')
            reqCounter = 0
            currTemp = cpu.temperature
            roomTemp, roomHum = readTemp()
            for element in (Const.tempLog, Const.varTempLog):
                with open(element, 'w') as out:
                    json.dump({"temp":roomTemp, "cptemp":currTemp, "hum":roomHum}, out)
            time.sleep(.8)
        
        # --------  00:00 switch ---------
        if time.strftime('%H:%M') == '00:00':
            with open(Const.lastFile, 'w') as out:    # get newest version of the "votes" dict and write it to the lastFile
                with open(Const.nowFile, 'r') as inp:
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
                kIn = json.loads(open(Const.KingFile, 'r').read())    # write everything to logs
                kIn[time.strftime('%d.%m.%Y')] = Highest
                with open(Const.KingFile, 'w') as out:
                    json.dump(kIn, out, indent=4)
                
                with open(Const.varLogFile, 'w') as out:
                    json.dump(kIn, out, indent=4)
                
                with open(Const.varKingLogFile, 'w') as out:
                    out.write(Highest)
                
                debug.debug(f"backed up files and logged the GayKing ({time.strftime('%H:%M')})\nGaymaster: {Highest}")
            
            else:
                debug.debug('no votes recieved')
            time.sleep(61)

        # -------- Fan Controller --------
        if t()-start1>=10:
            start1+=10
            resp = FanC.iter()
            if resp != True:
                debug.debug('Fan Controller Error\n'+resp)

############################################################################
#                              Main Program                                #
############################################################################
if __name__=='__main__':
    reqCounter = 0
    cpu = CPUTemperature()
    currTemp = cpu.temperature

    FanC = CPUHeatHandler()

    ClientKeys = dict() # list for Client AuthKeys
    
    Const = Constants()
    AccManager = manager(Const.crypFile)
    FunManager = FunctionManager()

    debug = Debug(Const.logFile)

    Vote = VOTES(Const.nowFile, Const.varNowFile)
    DV   = DoubleVote(Const.doubFile)

    with open(Const.logFile, 'w') as out:
        out.write('')

    dayRange = 30
    try:
        cal = json.load(open(Const.CalFile, 'r'))
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
        json.dump(cal, open(Const.CalFile, 'w'))

    except:
        cal = dict()
        tod = datetime.datetime.now()
        for i in range(dayRange, 0, -1):
            d = datetime.timedelta(days = i)
            a = tod - d
            dForm = f'{a.day}.{a.month}.{a.year}'
            cal[dForm] = list()
        json.dump(cal, open(Const.CalFile, 'w'))

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((Const.ip, Const.port))
        server.listen()
        debug.debug(Const.ip)

        #ServerRecv = Thread(target=recieve, daemon=True)
        Updater    = Thread(target=update, daemon=True)

        #ServerRecv.start()
        Updater.start()
        
        recieve()	
        #ServerRecv.join()

    except:
        server.shutdown(socket.SHUT_RDWR)
        debug.debug(format_exc())
        Terminate=True
        sys.exit(0)
