#! /usr/bin/python3
from fridrich import InvalidStringError
from gpiozero import CPUTemperature
import datetime, socket, time, json
from traceback import format_exc
from contextlib import suppress
from sys import exit as sExit
from threading import Thread
from typing import Any
from os import system
import socket

# local imports
from fridrich.cryption_tools import low, KeyFunc, MesCryp, NotEncryptedError
from fridrich.FanController import CPUHeatHandler
from fridrich.Accounts import manager
from fridrich.ServerFuncs import *
from fridrich.types import *

Const = Constants()
debug = Debug(Const.SerlogFile)

def sendSuccess(client:socket.socket) -> None:
    "send the success message to the client"
    Communication.send(client, {'Success':'Done'}, encryption = MesCryp.encrypt)

def verify(username:str, password:str, client:socket.socket) -> None:
    "verify the client and send result"
    global ClientKeys
    resp = AccManager.verify(username, password)
    IsValid = False
    key = None
    if resp == None:
        Communication.send(client, {'Error':'SecurityNotSet'}, encryption = MesCryp.encrypt)
        return

    elif resp:
        IsValid = True
        key = KeyFunc(ClientKeys, length=30)
        ClientKeys[key] = resp
        
    debug.debug(f'Username : {username}, Auth: {IsValid}')
    Communication.send(client, {'Auth':IsValid, 'AuthKey':key}, encryption = MesCryp.encrypt)    # send result to client

def dSendTraceback(func:FunctionType) -> FunctionType:
    "execute function and send traceback to client"
    def wrapper(*args, **kw):
        global client
        try:
            return func(*args, **kw)

        except Exception as e:
            with suppress(BrokenPipeError):
                error = str(type(e)).split("'")[1]
                info  = str(e)
                fullTraceback = format_exc()
                with suppress(UnboundLocalError):
                    Communication.send(client, {'Error':error, 'info':info, 'full':fullTraceback})
                with suppress((OSError, AttributeError, UnboundLocalError)):
                    client.close()

            debug.debug('Thread 1 error:')
            debug.debug(format_exc())
    return wrapper

@dSendTraceback
def clientHandler() -> None:
    "Handles communication with all clients"
    global server, reqCounter, ClientKeys, client
    try:
        client, mes = Communication.recieve(server, debug.debug, list(ClientKeys))
        if mes == None:
            Communication.send(client, {'Error':'MessageError', 'info':'Invalid Message/AuthKey'})
            return

    except NotEncryptedError:
        Communication.send(client, {'Error':'NotEncryptedError'})

    if mes['type'] == 'auth':   # authorization function
        verify(mes['Name'], mes['pwd'], client)

    elif mes['type'] == 'secReq':
        Communication.send(client, {'sec':ClientKeys[mes['AuthKey']][0]}, encryption=MesCryp.encrypt, key=mes['AuthKey'])

    else:
        if not 'AuthKey' in mes:    # if no AuthKey in message
            debug.debug('auth error, Key not in message')
            Communication.send(client, {'Error':'AuthError'}, encryption=MesCryp.encrypt)
            client.close()
            return

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
                Communication.send(client, {'Error':error, 'info':info, 'full':fullTraceback})
        
    client.close()  # close so it can be reused

@debug.catchTraceback
def temp_updater(starttime:float) -> None:
    "update the temperature"
    if time.time()-starttime>=1:    # every 2 seconds
        starttime+=1
        #s = str(reqCounter)
        #debug.debug(' Requests in last 2 seconds: '+'0'*(3-len(s))+s, end='\r')
        currTemp = cpu.temperature
        roomTemp, roomHum = readTemp()
        for element in (Const.tempLog, Const.varTempLog):
            with open(element, 'w') as out:
                json.dump({"temp":roomTemp, "cptemp":currTemp, "hum":roomHum}, out)
        time.sleep(.8)

@debug.catchTraceback
def ZSwitch(stime : str | None = '00:00') -> None:
    "if time is stime, execute the switch"
    if time.strftime('%H:%M') == stime:
        with open(Const.lastFile, 'w') as out:    # get newest version of the "votes" dict and write it to the lastFile
            with open(Const.nowFile, 'r') as inp:
                last = inp.read()
                out.write(last)

        Vote.set({'GayKing':dict()})
        
        # ---- Log File (only for GayKing Voting)
        last = json.loads(last)['GayKing'] # get last ones

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
            KingVar[time.strftime('%d.%m.%Y')] = Highest
            
            with open(Const.varKingLogFile, 'w') as out:
                out.write(Highest)
            
            debug.debug(f"backed up files and logged the GayKing ({time.strftime('%H:%M')})\nGayking: {Highest}")
        
        else:
            debug.debug('no votes recieved')
        if time.strftime('%a') == Const.DoubleVoteResetDay:  # if Monday, reset double votes
            dVotes = DV.value.get()
            for element in dVotes:
                dVotes[element] = Const.DoubleVotes
            DV.value.set(dVotes)

        time.sleep(61)

@debug.catchTraceback
def AutoReboot(rtime : str | None = "03:00") -> None:
    """
    if time is rtime, reboot the server (format is "HH:MM")
    
    if you don't want this, just set rtime to "99:99"

    or any other time that will never happen
    """
    if not len(rtime)==5 and rtime.replace(':', '').isnumeric():
        raise InvalidStringError('rtime needs to be formated like this: HH:MM')

    if time.strftime('%H:%M') == rtime:
        time.sleep(55)
        system('sudo reboot')

class DoubleVote:
    "Handle Double Votes"
    globals()
    def __init__(self, filePath:str) -> None:
        "filePath: path to file where doublevotes are saved"
        validUsers = json.loads(low.decrypt(open(Const.crypFile, 'r').read()))
        self.filePath = filePath

        try:
            value = load(open(self.filePath, 'r'))

        except FileNotFoundError:
            value = dict()
            for element in validUsers:
                value[element['Name']] = 1

        self.value = fileVar(value, self.filePath)

    def vote(self, vote:str, User:str) -> bool:
        """
        if the user has any double votes left,

        vote as "double-user"
        """
        global Vote

        value = self.value.get()
        if User in value:
            if value[User] < 1:
                return False
            try:
                Vote['GayKing'][User+'2'] = vote
            except KeyError:
                Vote['GayKing'] = dict()
                Vote['GayKing'][User+'2'] = vote

            value[User] -= 1
            self.value.set(value)
            return True
        
        value[User] = 0
        self.value.set(value)
        return False

    def unVote(self, User:str, voting:str) -> None:
        "unvote doublevote"
        global Vote

        with suppress(KeyError):
            Vote[voting].pop(User+'2')
        
            value = self.read()
            value[User]+=1
            self.value.set(value)
    
    def getFrees(self, User:str) -> int:
        "returns the free double-votes for the given users"
        value = self.value.get()
        if User in value:
            return value[User]

        return False

class FunctionManager:
    "manages the requested functions"
    def __init__(self):
        "init switch dict"
        self.switch = {
            'admin' : {
                'getUsers':AdminFuncs.getAccounts,
                'setPwd':AdminFuncs.setPassword,
                'setName':AdminFuncs.setUsername,
                'setSec':AdminFuncs.setSecurity,
                'newUser':AdminFuncs.addUser,
                'rmUser':AdminFuncs.rmUser,
                'end':AdminFuncs.end,
                'rsLogins':AdminFuncs.resetUserLogins,

                'setVersion':ClientFuncs.setVersion,
                'getVersion':ClientFuncs.setVersion,
                'gOuser':ClientFuncs.getOUser
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
                'getFrees':ClientFuncs.getFreeVotes,
                'gOuser':ClientFuncs.getOUser,
                'aChat':ClientFuncs.aChat,
                'gChat':ClientFuncs.gChat
            },
            'guest' : {                                  # instead of 5 billion if'S
                'CalEntry':ClientFuncs.CalendarHandler, 
                'req':ClientFuncs.reqHandler,
                'end':ClientFuncs.end,
            }
        }
    
    def exec(self, message:str, client:socket.socket) -> Tuple[bool, Any]:
        "execute the requested function or return error"
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
    "Manages the AdminFucntions"
    def getAccounts(message:str, client:socket.socket, *args) -> None:
        "get all users | passwords | clearances"
        acclist = AccManager.getAccs() # getting and decrypting accounts list
        Communication.send(client, acclist, encryption=MesCryp.encrypt) # sending list to client
    
    def setPassword(message:str, client:socket.socket, *args) -> None:
        "set a new password for the given user"
        AccManager.setPwd(message['User'], message['newPwd'])   # set new password
        sendSuccess(client) # send success

    def setUsername(message:str, client:socket.socket, *args) -> None:
        "change the username for the given user"
        AccManager.setUserN(message['OldUser'], message['NewUser']) # change account name 
        sendSuccess(client) # send success
    
    def setSecurity(message:str, client:socket.socket, *args) -> None:
        "change the clearance for the given user"
        AccManager.setUserSec(message['Name'], message['sec'])
        sendSuccess(client)

    def addUser(message:str, client:socket.socket, *args) -> None:
        "add a new user with set name, password and clearance"
        AccManager.newUser(message['Name'], message['pwd'], message['sec'])
        sendSuccess(client)
    
    def rmUser(message:str, client:socket.socket, *args) -> None:
        "remove user by username"
        AccManager.rmUser(message['Name'])
        sendSuccess(client)

    def resetUserLogins(message:str, client:socket.socket, *args) -> None:
        "reset all current logins (clear the ClientKeys variable)"
        global ClientKeys
        ClientKeys = dict()
        sendSuccess(client)

    def end(message:str, *args) -> None:
        "log-out user"
        with suppress(Exception):
            ClientKeys.pop(message['AuthKey'])

class ClientFuncs:
    "Manages the Client Functions"
    globals()
    def vote(message:str, client:socket.socket, *args) -> None:
        """
        vote a name
        
        votes user by username
        """
        global  Vote, ClientKeys
        resp = checkif(message['vote'], Vote.get(), message['voting'])
        name = ClientKeys[message['AuthKey']][1]
        if not message['voting'] in Vote:
            Vote[message['voting']] = dict()
        Vote[message['voting']][name] = resp    # set vote
        debug.debug(f'got vote: {message["vote"]}                     .')   # print that it recievd vote (debugging)

        sendSuccess(client)
    
    def unvote(message:str, client:socket.socket, *args) -> None:
        "unvote a user"
        global nowFile, Vote
        name = ClientKeys[message['AuthKey']][1] # WHY U NOT WORKING
        with suppress(KeyError): 
            del Vote[message['voting']][name]  # try to remove vote from client, if client hasn't voted yet, ignore it

        sendSuccess(client)
    
    def CalendarHandler(message:str, client:socket.socket, *args) -> None:
        "Handle the Calendar requests/write"
        global CalFile
        cal = json.load(open(Const.CalFile, 'r'))
        if not message['event'] in cal[message['date']]:    # if event is not there yet, create it
            try:
                cal[message['date']].append(message['event'])
            except (KeyError, AttributeError):
                cal[message['date']] = [message['event']]

            json.dump(cal, open(Const.CalFile, 'w'))  # update fil
            debug.debug(f'got Calender: {message["date"]} - "{message["event"]}"')    # notify that threr has been a calendar entry
        
        sendSuccess(client)

    def reqHandler(message:str, client:socket.socket, *args) -> None:
        "Handle some default requests / logs"
        global reqCounter, nowFile, Vote, lastFile
        reqCounter+=1
        if message['reqType']=='now':   # now is for the current "votes" dictionary
            with open(Const.nowFile, 'r') as inp:
                Communication.send(client, json.load(inp), encryption=MesCryp.encrypt, key=message['AuthKey'])

        elif message['reqType'] == 'last':  # last is for the "votes" dictionary of the last day
            with open(Const.lastFile, 'r') as inp:
                Communication.send(client, json.load(inp), encryption=MesCryp.encrypt, key=message['AuthKey'])
                
        elif message['reqType'] == 'log':   # returns the log of the GayKings
            with open(Const.KingFile, 'r') as inp:
                Communication.send(client, json.load(inp), encryption=MesCryp.encrypt, key=message['AuthKey'])
                
        elif message['reqType'] == 'attds': # returns All attendants (also non standart users)
            newones = getNewones(message['atype'], Vote, Const.lastFile, message['voting'])  
            Communication.send(client, {'Names':['Lukas', 'Niclas', 'Melvin']+newones}, encryption=MesCryp.encrypt, key=message['AuthKey'])    # return stardart users + new ones
                
        elif message['reqType'] == 'temps': # returns the temperatures
            rtemp, rhum = readTemp()
            Communication.send(client, {'Room':rtemp, 'CPU':currTemp, 'Hum':rhum}, encryption=MesCryp.encrypt, key=message['AuthKey'])
                
        elif message['reqType'] == 'cal':   # returns the calendar dictionary
            with open(Const.CalFile, 'r') as inp:
                Communication.send(client, json.load(inp), encryption=MesCryp.encrypt, key=message['AuthKey'])
                
        else:   # notify if an invalid request has been sent
            debug.debug(f'Invalid Request {message["reqType"]}')

    def changePwd(message:str, client:socket.socket,  *args) -> None:
        "change the password of the user (only for logged in user)"
        global ClientKeys
        validUsers = json.loads(low.decrypt(open(Const.crypFile, 'r').read()))
        name = ClientKeys[message['AuthKey']][1]
        for element in validUsers:
            if element['Name'] == name:
                element['pwd'] = message['newPwd']
        
        with open(Const.crypFile, 'w') as out:
            fstring = json.dumps(validUsers, ensure_ascii=False)
            cstring = low.encrypt(fstring)
            out.write(cstring)
        
        sendSuccess(client)

    def getVote(message:str, client:socket.socket, *args) -> None:
        "get the vote of the logged-in user"
        if 'flag' in message:
            x = '2' if message['flag'] == 'double' else ''
        else:
            x = ''

        name = ClientKeys[message['AuthKey']][1] + x
        if not message['voting'] in Vote:
            Communication.send(client, {'Error':'NotVoted'}, encryption=MesCryp.encrypt, key=message['AuthKey'])
            return

        if not name in Vote[message['voting']]:
            Communication.send(client, {'Error':'NotVoted'}, encryption=MesCryp.encrypt, key=message['AuthKey'])
            return
        cVote = Vote[message['voting']][name]
        Communication.send(client, {'Vote':cVote}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    def getVersion(message:str, client:socket.socket, *args) -> None:
        "read the Version variable"
        vers = open(Const.versFile, 'r').read()
        Communication.send(client, {'Version':vers}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    def setVersion(message:str, client:socket.socket, *args) -> None:
        "set the version variable"
        with open(Const.versFile, 'w') as out:
            out.write(message['version'])

        sendSuccess(client)

    def DoubVote(message:str, client:socket.socket, *args) -> None:
        "double vote"
        global DV, Vote
        name = ClientKeys[message['AuthKey']][1]
        resp = checkif(message['vote'], Vote.get(), message['voting'])     
        resp = DV.vote(resp, name)
        if resp:
            sendSuccess(client)
        else:
            Communication.send(client, {'Error':'NoVotes'}, encryption=MesCryp.encrypt, key=message['AuthKey'])
    
    def DoubUnVote(message:str, client:socket.socket, *args) -> None:
        "double unvote"
        global DV
        name = ClientKeys[message['AuthKey']][1]
        DV.unVote(name, message['voting'])
        sendSuccess(client)
    
    def getFreeVotes(message:str, client:socket.socket, *args) -> None:
        "get free double votes of logged in user"
        global DV
        name = ClientKeys[message['AuthKey']][1]
        frees = DV.getFrees(name)

        if frees == False and frees != 0:
            Communication.send(client, {'Error':'RegistryError'}, encryption=MesCryp.encrypt, key=message['AuthKey'])
            return
        Communication.send(client, {'Value':frees}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    def getOUser(message:str, client:socket.socket, *args) -> None:
        "get all logged in users"
        global ClientKeys
        names = list()
        for element in ClientKeys:
            names.append(ClientKeys[element][1])
        
        Communication.send(client, {'users':names}, encryption=MesCryp.encrypt, key=message['AuthKey'])


    def aChat(message:str, client:socket.socket, *args) -> None:
        "Add message to chat"
        name = ClientKeys[message['AuthKey']][1]
        Chat.add(message['message'], name)
        sendSuccess(client)
    
    def gChat(message:str, client:socket.socket, *args) -> None:
        "get Chat"
        resp = Chat.get()
        Communication.send(client, resp, encryption=MesCryp.encrypt, key=message['AuthKey'])


    def end(message:str, *args) -> None:
        "clear logged in user"
        global ClientKeys
        with suppress(Exception):
            ClientKeys.pop(message['AuthKey'])

def recieve() -> None:
    "Basicly the whole server"
    while not Const.Terminate:
        clientHandler()

def update() -> None:
    "updates every few seconds"
    global currTemp, reqCounter, FanC, UpDebug
    start = time.time()
    start1 = start
    while not Const.Terminate:
        # ----- Temperature updater ------
        temp_updater(start)
        
        # --------  00:00 switch ---------
        ZSwitch(Const.switchTime)

        # --------- daily reboot ---------
        AutoReboot(Const.rebootTime)

        # -------- Fan Controller --------
        if time.time()-start1>=10:
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
    
    AccManager = manager(Const.crypFile)
    FunManager = FunctionManager()

    UpDebug = Debug(Const.SerUpLogFile)

    Vote = fileVar({}, (Const.nowFile, Const.varNowFile))
    DV   = DoubleVote(Const.doubFile)
    KingVar = fileVar(load(open(Const.KingFile, 'r')), (Const.KingFile, Const.varLogFile))

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
            except KeyError:
                cal[dForm] = list()
        json.dump(cal, open(Const.CalFile, 'w'))

    except Exception:
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
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((Const.ip, Const.port))
        server.listen()
        debug.debug(Const.ip)

        client = None

        Updater = Thread(target=update, daemon=True)

        Updater.start()
        
        recieve()

    except:
        server.shutdown(socket.SHUT_RDWR)
        debug.debug(format_exc())
        Terminate=True
        sExit(0)
