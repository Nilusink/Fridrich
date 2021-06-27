#! /usr/bin/python3
from gpiozero import CPUTemperature
import datetime, socket, time, json
from traceback import format_exc
from contextlib import suppress
from threading import Thread
from random import sample
import sys

# local imports
from modules.cryption_tools import low, KeyFunc, MesCryp, NotEncryptedError
from modules.FanController import CPUHeatHandler
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

def sendSuccess(client):
    Communication.send(client, {'Success':'Done'}, encryption = MesCryp.encrypt)

def verify(username, password, client):
    resp = AccManager.verify(username, password)
    IsValid = False
    key = None
    if resp == None:
        Communication.send(client, {'Error':'SecurityNotSet'}, encryption = MesCryp.encrypt)
        return

    elif resp:
        IsValid = True
        key = KeyFunc(length=30)
        ClientKeys[key] = resp
        
    debug.debug(f'Username : {username}, Auth: {IsValid}')
    Communication.send(client, {'Auth':IsValid, 'AuthKey':key}, encryption = MesCryp.encrypt)    # send result to client

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
        Communication.send(client, acclist, encryption=MesCryp.encrypt) # sending list to client
    
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

        sendSuccess(client)
    
    def unvote(message, client, *args):
        global nowFile, Vote
        votes = Vote.get()    # update votes
        name = ClientKeys[message['AuthKey']][1] # WHY U NOT WORKING
        with suppress(KeyError): 
            del votes[name]  # try to remove vote from client, if client hasn't voted yet, ignore it
        Vote.write(votes) # update file

        sendSuccess(client)
    
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
        
        sendSuccess(client)

    def reqHandler(message, client, *args):
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
            newones = getNewones(message['atype'], Vote, Const.lastFile)  
            Communication.send(client, {'Names':['Lukas', 'Niclas', 'Melvin']+newones}, encryption=MesCryp.encrypt, key=message['AuthKey'])    # return stardart users + new ones
                
        elif message['reqType'] == 'temps': # returns the temperatures
            rtemp, rhum = readTemp()
            Communication.send(client, {'Room':rtemp, 'CPU':currTemp, 'Hum':rhum}, encryption=MesCryp.encrypt, key=message['AuthKey'])
                
        elif message['reqType'] == 'cal':   # returns the calendar dictionary
            with open(Const.CalFile, 'r') as inp:
                Communication.send(client, json.load(inp), encryption=MesCryp.encrypt, key=message['AuthKey'])
                
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
        
        sendSuccess(client)

    def getVote(message, client, *args):
        votes = Vote.get()
        if 'flag' in message:
            x = '2' if message['flag'] == 'double' else ''
        else:
            x = ''

        name = ClientKeys[message['AuthKey']][1] + x
        if not name in Vote.get():
            Communication.send(client, {'Error':'NotVoted'}, encryption=MesCryp.encrypt, key=message['AuthKey'])
            return
        cVote = votes[name]
        Communication.send(client, {'Vote':cVote}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    def getVersion(message, client, *args):
        vers = open(Const.versFile, 'r').read()
        Communication.send(client, {'Version':vers}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    def setVersion(message, client, *args):
        with open(Const.versFile, 'w') as out:
            out.write(message['version'])

        sendSuccess(client)

    def DoubVote(message, client, *args):
        global DV, Vote
        name = ClientKeys[message['AuthKey']][1]
        resp = checkif(message['vote'], Vote.get())     
        resp = DV.vote(resp, name)
        if resp:
            sendSuccess(client)
        else:
            Communication.send(client, {'Error':'NoVotes'}, encryption=MesCryp.encrypt, key=message['AuthKey'])
    
    def DoubUnVote(message, client, *args):
        global DV
        name = ClientKeys[message['AuthKey']][1]
        DV.unVote(name)
        sendSuccess(client)
    
    def getFreeVotes(message, client, *args):
        global DV
        name = ClientKeys[message['AuthKey']][1]
        frees = DV.getFrees(name)

        if frees == False and frees != 0:
            Communication.send(client, {'Error':'RegistryError'}, encryption=MesCryp.encrypt, key=message['AuthKey'])
            return
        Communication.send(client, {'Value':frees}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    def end(message, *args):
        global ClientKeys
        with suppress(Exception):
            ClientKeys.pop(message['AuthKey'])

def recieve():  # Basicly the whole server
    global server, reqCounter, ClientKeys
    while not Const.Terminate:
        try:
            try:
                client, mes = Communication.recieve(server, debug.debug, list(ClientKeys))
            except NotEncryptedError:
                Communication.send(client, {'Error':'NotEncryptedError'})
            if mes['type'] == 'auth':   # authorization function
                verify(mes['Name'], mes['pwd'], client)

            elif mes['type'] == 'secReq':
                Communication.send(client, {'sec':ClientKeys[mes['AuthKey']][0]}, encryption=MesCryp.encrypt, key=mes['AuthKey'])

            else:
                if not 'AuthKey' in mes:    # if no AuthKey in message
                    debug.debug('auth error, Key not in message')
                    Communication.send(client, {'Error':'AuthError'}, encryption=MesCryp.encrypt, key=mes['AuthKey'])
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
                        Communication.send(client, {'Error':error, 'info':info, 'full':fullTraceback}, encryption=MesCryp.encrypt)
                
            client.close()  # close so it can be reused

        except Exception as e:
            with suppress(BrokenPipeError):
                error = str(type(e)).split("'")[1]
                info  = str(e)
                fullTraceback = format_exc()
                Communication.send(client, {'Error':error, 'info':info, 'full':fullTraceback}, encryption=MesCryp.encrypt)
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

    debug = Debug(Const.SerlogFile)

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

        Updater = Thread(target=update, daemon=True)

        Updater.start()
        
        recieve()

    except:
        server.shutdown(socket.SHUT_RDWR)
        debug.debug(format_exc())
        Terminate=True
        sys.exit(0)
