import socket, json

# local imports
import modules.err_classes as err
from modules.useful import Dict

############################################################################
#                             other functions                              #
############################################################################
def jsonRepair(string:str):
    parts = string.split('}{')
    if len(parts)>1:
        return parts[0]+'}'
    return string

############################################################################
#                      Server Communication Class                          #
############################################################################
class Connection:
    def __init__(self):
        self.ServerIp = socket.gethostbyname('fridrich')    # get ip of fridrich
        print('Server IP: '+self.ServerIp)
        self.port = 12345   # set communication port with server

        self.AuthKey = None 

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
        
        else:
            st = f'Error: {error}\nInfo: {args[0]["info"] if "info" in args[0] else "None"}'
            raise err.UnknownError('An Unknown Error Occured: \n'+st)

    def send(self, dictionary:dict):
        self.reconnect() # reconnect to the server

        dictionary['AuthKey'] = self.AuthKey    # add AuthKey to the dictionary
        msg = json.dumps(dictionary).encode('utf-8')    # convert to bytes
        self.Server.send(msg)   # send request

    def recieve(self, length=1024):
        msg = ''
        while msg=='':
            msg = jsonRepair(self.Server.recv(length).decode('utf-8'))  # recieve message
        try:    # test if message is valid json message
            msg = json.loads(msg)
        except json.JSONDecodeError:    # if not raise error
            print(f'Message: "{msg}"')
            self.errorHandler(msg)

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

    def auth(self, username:str, password:str):
        msg = {  # message
            'type':'auth',
            'Name':username,
            'pwd':password
        }
        self.send(msg)  # send message
        resp = self.recieve()   # recieve authKey (or error)

        self.AuthKey = resp['AuthKey']

        return resp['Auth'] # return True or False

    def getAttendants(self, flag = 'now'): # flag can be 'now' or 'last'
        self.send({'type':'req', 'reqType':'attds', 'atype':flag})  # send message
        resp = self.recieve()   # get response

        return resp['Names']    # return names

    def sendVote(self, *args, flag = 'vote'): # flag can be 'vote', 'unvote', 'dvote' or 'dUvote'
        if flag in ('vote', 'dvote'):
            msg = {'type':flag, 'vote':args[0]} # if vote send vote
        else:
            msg = {'type':flag} # if no vote send no vote
        
        self.send(msg)  # send vote
        self.recieve()  # recieve success or error
    
    def getResults(self, flag = 'now'): # flag can be 'now', 'last'
        msg = {'type':'req', 'reqType':flag}    # set message
        self.send(msg)  # send message

        res = self.recieve()    # get response

        attds = dict()  # create dictionary with all attendants:votes
        for element in [res[element] for element in res]+['Lukas', 'Niclas', 'Melvin']:
            attds[element] = int()

        votes = int()
        for element in res: # assign votes to attendant
            votes+=1
            attds[res[element]]+=1
        
        return votes, attds # retur total votes and dict
    
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

    def getVote(self, flag='normal'):   # flag can be normal or double
        mes = {'type':'getVote', 'flag':flag}    # set message
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


    def AdminGetUsers(self):
        msg = {'type':'getUsers'}
        self.send(msg)
        resp = self.recieve()
        return resp
    
    def AdminSetPassword(self, User, Password):
        msg = {'type':'setPwd', 'User':User, 'newPwd':Password}
        self.send(msg)
        self.recieve()
    
    def AdminSetUsername(self, OldUsername, NewUsername):
        msg = {'type':'setName', 'OldUser':OldUsername, 'NewUser':NewUsername}
        self.send(msg)
        self.recieve()

    def AdminSetSecurity(self, username, password):
        msg = {'type':'setSec', 'Name':username, 'sec':password}
        self.send(msg)
        self.recieve()

    def AdminAddUser(self, username, password, clearance):
        msg = {'type':'newUser', 'Name':username, 'pwd':password, 'sec':clearance}
        self.send(msg)
        self.recieve()

    def end(self):
        msg = {'type':'end'}    # set message
        self.send(msg)  # send message
############################################################################
#                   Class for Searching Wolfram Alpha                      #
############################################################################
# class wiki:
#     def __init__(self):
#         # App id obtained by the above steps
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