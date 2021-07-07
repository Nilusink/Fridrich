from os import popen
import socket, json

# local imports
from fridrich.cryption_tools import tryDecrypt, NotEncryptedError, MesCryp
import fridrich.err_classes as err
from fridrich.useful import Dict
import fridrich as fr

############################################################################
#                             other functions                              #
############################################################################
def jsonRepair(string:str): # if two messages are scrambled together, split them and use the first one
    parts = string.split('}{')  # happens sometimes, probably because python is to slow
    if len(parts)>1:
        return parts[0]+'}'
    return string

def getWifiName():
    ret = popen('Netsh WLAN show interfaces').readlines()   # read interface infos
    wifiDict = dict()
    for element in ret:
        tmp = element.split(':')
        if len(tmp)>1:  # if element is seperated with ":" then make it dict
            wifiDict[tmp[0].lstrip().rstrip()] = ':'.join(tmp[1::]).lstrip().rstrip().replace('\n', '')
    
    return wifiDict['SSID']

def dateforsort(message):   # go from format "hour:minute:second:millisecond - day.month.year" to "year.month.day - hour:minute:second:millisecond"
    y = message['time'].split(' - ')    # split date and time
    return '.'.join(reversed(y[1].split('.')))+' - '+y[0]   # reverse date and place time at end

############################################################################
#                      Server Communication Class                          #
############################################################################
class Connection:
    def __init__(self, debugmode=fr.Off):
        self.debugmode = debugmode

        self.ServerIp = socket.gethostbyname('fridrich')    # get ip of fridrich
        if self.debugmode in ('normal', 'full'):
            print(fr.bcolors.OKGREEN+'Server IP: '+self.ServerIp+fr.bcolors.ENDC)
        self.port = 12345   # set communication port with server

        self.AuthKey = None 
        self.userN = None

    # "local" functions
    def errorHandler(self, error:str, *args):
        if error == 'AccessError':
            raise err.AccessError('Access denied')
        
        elif error == 'AuthError':
            raise err.AuthError('Authentification failed')
        
        elif error == 'NotVoted':
            raise NameError('Not Voted')
        
        elif error == 'json':
            raise err.JsonError('Crypled message')
        
        elif error == 'NoVotes':
            raise err.NoVotes('No Votes left')

        elif error == 'RegistryError':
            raise err.RegistryError('Not registered')
        
        elif error == 'SwitchToUser':
            raise err.NotAUser('Switch to user account to vote')
        
        elif error == 'InvalidRequest':
            raise err.InvalidRequest('Invalid erquest: '+args[0]['info'])
        
        elif error == 'SecurityNotSet':
            raise err.SecutiryClearanceNotSet('Security clearance not set! Contact administrator')
        
        elif error == 'NotEncryptedError':
            raise NotEncryptedError('You just send a not encrypted message. How tf did you do that??')
        
        elif error == 'NameError':
            raise NameError('Username Already exits')
        
        elif error == 'MessageError':
            raise err.MessageError(args[0]['info'])

        else:
            if self.debugmode == 'full':
                st = f'Error: {error}\nInfo: {args[0]["info"] if "info" in args[0] else "None"}\nFullBug: {args[0]["full"] if "full" in args[0] else "None"}'
            elif self.debugmode == 'normal':
                st = f'Error: {error}\nInfo: {args[0]["info"] if "info" in args[0] else "None"}'

            else:
                raise err.UnknownError(f'A Unknown Error Occured:\nError: {error}')

        raise err.UnknownError('An Unknown Error Occured: \n'+st)

    def send(self, dictionary:dict):
        self.reconnect() # reconnect to the server
        
        if self.AuthKey:
            # add AuthKey to the dictionary+
            dictionary['AuthKey'] = self.AuthKey
            stringMes = json.dumps(dictionary, ensure_ascii=False)
            mes = MesCryp.encrypt(stringMes, key=self.AuthKey.encode())
            self.Server.send(mes)
            if self.debugmode in ('normal', 'full'):
                print(dictionary)
                print(stringMes)
            if self.debugmode == 'full':
                print(mes)
            return

        stringMes = json.dumps(dictionary, ensure_ascii=False)
        self.Server.send(MesCryp.encrypt(stringMes))
        if self.debugmode in ('normal', 'full'):
            print(stringMes)

    def recieve(self, length=2048):
        msg = ''
        while msg=='':
            mes = self.Server.recv(length)
            if self.debugmode == 'full':
                print(fr.bcolors.WARNING+str(mes)+fr.bcolors.ENDC)
            msg = tryDecrypt(mes, [self.AuthKey], errors=False)

            if msg == None:
                msg = {'Error':'MessageError', 'info':'Server message receved is not valid'}
            if self.debugmode in ('normal', 'full'):
                print(fr.bcolors.OKCYAN+str(msg)+fr.bcolors.ENDC)

        if 'Error' in msg:  # if error was send by server
            success = False
        else:
            success = True

        if success:
            return msg  # if no error was detected, return dict
        
        self.errorHandler(msg['Error'], msg) #raise error if serverside-error

    def reconnect(self):
        try:    # try to reconnect to the server
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create socket instance
            self.Server.connect((self.ServerIp, self.port)) # connect to server
        except socket.error:
            raise ValueError

    # user functions
    def auth(self, username:str, password:str):
        msg = {  # message
            'type':'auth',
            'Name':username,
            'pwd':password
        }
        self.userN = username
        self.AuthKey = None # reset AuthKey
        self.send(msg)  # send message
        resp = self.recieve()   # recieve authKey (or error)

        self.AuthKey = resp['AuthKey']

        return resp['Auth'] # return True or False

    def getSecClearance(self):
        msg = {'type':'secReq'}
        self.send(msg)
        resp = self.recieve()
        return resp['sec']

    def getAttendants(self, flag = 'now', voting = 'GayKing'): # flag can be 'now' or 'last'
        self.send({'type':'req', 'reqType':'attds', 'atype':flag, 'voting':voting})  # send message
        resp = self.recieve()   # get response

        return resp['Names']    # return names

    def sendVote(self, *args, flag = 'vote', voting = 'GayKing'):   # flag can be 'vote', 'unvote', 'dvote' or 'dUvote', voting is custom
        msg = {'type':flag, 'voting':voting}                        # DoubleVotes are only available for GayKing voting and other voting 
        if flag in ('vote', 'dvote'):                               # types will be ignored if flag is 'dvote'
            msg['vote'] = args[0] # if vote send vote
        
        self.send(msg)  # send vote
        self.recieve()  # recieve success or error
    
    def getResults(self, flag = 'now'): # flag can be 'now', 'last', will return Voting:'results':VoteDict and
        msg = {'type':'req', 'reqType':flag}    # set message                    Voting:'totalVotes':TotalVotes
        self.send(msg)  # send message

        res = self.recieve()    # get response

        out = dict()
        for voting in res:
            attds = dict()  # create dictionary with all attendants:votes
            nowVoting = res[voting]
            for element in [nowVoting[element] for element in nowVoting]+(['Lukas', 'Niclas', 'Melvin'] if voting=='GayKing' else []):
                attds[element] = 0

            votes = int()
            for element in res[voting]: # assign votes to attendant
                votes+=1
                attds[res[voting][element]]+=1
            out[voting] = dict()
            out[voting]['totalVotes'] = votes
            out[voting]['results'] = attds
        
        return out # retur total votes and dict
    
    def getLog(self):
        msg = {'type':'req', 'reqType':'log'}   # set message
        self.send(msg)  # send request

        res = self.recieve()    # get response
        return res  # return response

    def getStreak(self):
        log = self.getLog() # get log dictionary

        sortedlog = {x:log[x] for x in sorted(log, key=lambda x: '.'.join(reversed(x.split('.'))) )}    # sort list by year, month, date

        fullList = list(reversed(list(Dict.Values(sortedlog)))) # get list of all Kings
        StreakGuys = list(fullList[0].split('|'))   # if a|b|c make list of (a, b, c), else just (a)

        StreakDict = {StreakGuy:int() for StreakGuy in StreakGuys}  # create Dictionary with scheme: {a:0, b:0, c:0}
        for StreakGuy in StreakGuys:    # iterate all guys
            for element in fullList:    # iterate all votes
                if StreakGuy.lower() in element.lower():    # guy was in previous vote
                    StreakDict[StreakGuy]+=1    # add to streak and continue
                else:
                    break   # else begin with new guy

        iDict = Dict.inverse(StreakDict)    # inversed Dict ({1:a, 3:b, 0:c} instead of {a:1, b:3, c:0})
        Name = iDict[max(iDict)]    # get name of the guy with max streak
        Streak = StreakDict[Name]   # get streak by name
        
        return Name, Streak # return results

    def getTemps(self):
        msg = {'type':'req', 'reqType':'temps'} # set message
        self.send(msg)  # send message

        res = self.recieve()    # get response

        return res['Room'], res['CPU'], res['Hum']  # return room and cpu temperature
    
    def getCal(self):
        msg = {'type':'req', 'reqType':'cal'}   # set message
        self.send(msg)  # send request

        res = self.recieve()    # get response
        return res  # return response

    def sendCal(self, date:str, event:str):
        msg = {'type':'CalEntry', 'date':date, 'event':event}   # set message
        self.send(msg)  # send message
        self.recieve()  # recieve response (success, error)

    def changePwd(self, newPassword:str):
        mes = {'type':'changePwd', 'newPwd':newPassword}    # set message
        self.send(mes)  # send message
        self.recieve()  # get response (success, error)

    def getVote(self, flag = 'normal', voting = 'GayKing'):   # flag can be normal or double
        mes = {'type':'getVote', 'flag':flag, 'voting':voting}    # set message
        self.send(mes)  # send request

        resp = self.recieve()   # get response

        return resp['Vote'] # return vote

    def getVersion(self):
        mes = {'type':'getVersion'} # set message
        self.send(mes)  # send request
        resp = self.recieve()   # get response

        return resp['Version']  # return version

    def setVersion(self, version:str):
        mes = {'type':'setVersion', 'version':version}  # set message
        self.send(mes)  # send message
        self.recieve()  # get response (success, error)

    def getFrees(self):
        msg = {'type':'getFrees'}
        self.send(msg)
        resp = self.recieve()
        return resp['Value']

    def getOnlineUsers(self):
        msg = {'type':'gOuser'}
        self.send(msg)
        users = self.recieve()['users']
        return users

    def sendChat(self, message):
        msg = {'type':'aChat', 'message':message}
        self.send(msg)
        self.recieve()
    
    def getChat(self):
        msg = {'type':'gChat'}
        self.send(msg)
        raw = self.recieve(length=1048576)
        out = sorted(raw, key = dateforsort)
        return out

    # Admin Functions
    def AdminGetUsers(self):
        msg = {'type':'getUsers'}
        self.send(msg)
        resp = self.recieve()
        return resp
    
    def AdminSetPassword(self, User:str, Password:str):
        msg = {'type':'setPwd', 'User':User, 'newPwd':Password}
        self.send(msg)
        self.recieve()
    
    def AdminSetUsername(self, OldUsername:str, NewUsername:str):
        msg = {'type':'setName', 'OldUser':OldUsername, 'NewUser':NewUsername}
        self.send(msg)
        self.recieve()

    def AdminSetSecurity(self, username:str, password:str):
        msg = {'type':'setSec', 'Name':username, 'sec':password}
        self.send(msg)
        self.recieve()

    def AdminAddUser(self, username:str, password:str, clearance:str):
        msg = {'type':'newUser', 'Name':username, 'pwd':password, 'sec':clearance}
        self.send(msg)
        self.recieve()

    def AdminRemoveUser(self, username:str):
        msg = {'type':'rmUser', 'Name':username}
        self.send(msg)
        self.recieve()

    def AdminResetLogins(self):
        msg = {'type':'rsLogins'}
        self.send(msg)
        self.recieve()

    # some other functions
    def __repr__(self):
        return f'Backend instance (debugmode: {self.debugmode}, user: {self.userN}, authkey: {self.AuthKey})'
    
    def __str__(self):  # return string of information when str() is called
        return self.__repr__()

    def __iter__(self): # return dict of information when dict() is called
        d = {'debugmode':self.debugmode, 'user':self.userN, 'authkey':self.AuthKey}
        for element in d:
            yield (element, d[element])

    # def __del__(self):  # end connection if class instance is deleted # caused some issues where it got called without actually calling it
    #     self.end()

    def __nonzero__(self):  # return True if AuthKey
        return bool(self.AuthKey)

    def __bool__(self): # return False if not AuthKey
        return self.__nonzero__()

    # the end
    def end(self):
        msg = {'type':'end'}    # set message
        self.send(msg)  # send message
############################################################################
#                   Class for Searching Wolfram Alpha                      #
############################################################################
# class wiki:
#     def __init__(self):
#         app_id = 'U3ETL7-RL45EG5R6Y'
#         # Instance of wolf ram alpha 
#         # client class
#         self.client = Client(app_id)
    
#     def getInfos(self, keyword):
#         # Stores the response from 
#         # wolf ram alpha
#         res = self.client.query(keyword)
#         resDict = dict()
#         if res['@success']:
#             for element in res['pod']:
#                 t = element['@title']
#                 with suppress(TypeError):
#                     resDict[t] = element['subpod']['plaintext']
#         return resDict