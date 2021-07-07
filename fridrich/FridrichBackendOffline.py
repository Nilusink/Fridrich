# to test some functions without the need to be connected to Fridrich
from contextlib import suppress
from datetime import datetime
import time

# local imports
import fridrich.err_classes as err
from fridrich.useful import Dict

############################################################################
#                             other functions                              #
############################################################################
def getWifiName():
    return 'Fridrich'

def dateforsort(message):   # go from format "hour:minute - day.month.year" to "year.month.day - hour:minute"
    y = message['time'].split(' - ')    # split date and time
    return '.'.join(reversed(y[1].split('.')))+' - '+y[0]   # reverse date and place time at end

############################################################################
#                      Server Communication Class                          #
############################################################################
class Connection:
    def __init__(self, mode='normal'):
        self.mode = mode

        self.ServerIp = '127.0.0.1'#socket.gethostbyname('fridrich')    # get ip of fridrich
        if self.mode == 'debug':
            print('Server IP: '+self.ServerIp)
        #self.port = 12345   # set communication port with server

        self.AuthKey = None 
        self.yes = {
            'GayKing':{
                'Melvin':'Hurensohn',
                'Lukas':'Busfahrer',
                'Niclas':'SockenTyp'
            }
        }

        self.now = {
            'GayKing':{}
        }

        self.users = {
            'Niclas',
            'Melvin',
            'Lukas'
        }

        self.dVotes = {user:1 for user in self.users}

        self.CurrUser = None
        self.log = {
            '20.06.2021':'Melvin',
            '21.06.2021':'Lukas|Busfahrer',
            '22.06.2021':'Niclas|Busfahrer',
            '23.06.2021':'Melvin|Lukas|Niclas|Busfahrer',
            '24.06.2021':'Busfahrer',
            '25.06.2021':'busfahrer',
            '26.06.2021':'Melvin|Busfahrer',
            '27.06.2021':'Busfahrer',
            '28.06.2021':'busfahrer',
            '29.06.2021':'Busfahrer',
            '30.06.2021':'Busfahrer',
            '01.07.2021':'Busfahrer|SockenTyp|jesus',
            '02.07.2021':'Busfahrer|Melvin'
        }

        self.Calendar = dict()

        self.version = '11.11.11'
        self.chat = list()

    # user functions
    def auth(self, username:str, password:str):
        if username in self.users:
            self.CurrUser = username
            return True
        return False

    def getSecClearance(self):
        return 'user'

    def getAttendants(self, flag = 'now', voting = 'GayKing'): # flag can be 'now' or 'last'
        attds = self.users + [element for element in Dict.Values(self.now[voting])]

        return attds    # return names

    def sendVote(self, *args, flag = 'vote', voting = 'GayKing'):   # flag can be 'vote', 'unvote', 'dvote' or 'dUvote', voting is custom
        if not self.CurrUser:
            raise err.AuthError('Not signed in')
        if flag in ('vote', 'dvote'):
            if not voting in self.now:
                self.now[voting] = dict()
            name = self.CurrUser + ('2' if flag=='dvote' else '')
            self.now[voting][name] = args[0]
        
        elif flag in ('unvote', 'dUvote'):
            name = self.CurrUser + ('2' if flag=='dUvote' else '')
            with suppress(KeyError):
                del self.now[voting][name]
        
        else:
            raise err.InvalidRequest(f'Unknown flag "{flag}"')
    
    def getResults(self, flag = 'now'): # flag can be 'now', 'last', will return Voting:'results':VoteDict and
        if flag == 'now':
            res = self.now
        elif flag == 'last':
            res = self.yes
        
        else: 
            raise err.InvalidRequest(f'Unkown flag "{flag}"')

        out = dict()
        for voting in res:
            attds = dict()  # create dictionary with all attendants:votes
            nowVoting = res[voting]
            print(nowVoting)
            for element in [nowVoting[element] for element in nowVoting]+['Lukas', 'Niclas', 'Melvin']:
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
        return self.log

    def getStreak(self):
        log = self.log # get log dictionary

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
        return 26.34, 37.127, 35.98  # return room and cpu temperature
    
    def getCal(self):
        return self.Calendar

    def sendCal(self, date:str, event:str):
        if not date in self.Calendar:
            self.Calendar[date] = list()

        self.Calendar[date].append(event)
        
    def changePwd(self, newPassword:str):
        0

    def getVote(self, flag = 'normal', voting = 'GayKing'):   # flag can be normal or double
        if not self.CurrUser:
            raise err.AuthError('Not signed in')
        user = self.CurrUser + ('2' if flag=='double' else '')
        try:
            vote = self.now[voting][user]
        except KeyError:
            raise NameError('NotVoted')
        return vote # return vote

    def getVersion(self):
        return self.version

    def setVersion(self, version:str):
        self.version = version

    def getFrees(self):
        if not self.CurrUser:
            raise err.AuthError('Not signed in')
        name = self.CurrUser
        return self.dVotes[name]

    def getOnlineUsers(self):
        if not self.CurrUser:
            raise err.AuthError('Not sigend in')
        return self.CurrUser

    def sendChat(self, message):
        curr_time = datetime.now()
        formatted_time = curr_time.strftime('%H:%M:%S.%f')+time.strftime(' - %d.%m.%Y')
        self.chat.append({'time':formatted_time, 'name':self.CurrUser, 'content':message})
    
    def getChat(self):
        out = sorted(self.chat, key = dateforsort)
        return out

    # some other functions
    def __repr__(self):
        return f'Backend instance (mode: {self.mode}, user: {self.CurrUser}, authkey: {self.AuthKey})'
    
    def __str__(self):  # return string of information when str() is called
        return self.__repr__()

    def __iter__(self): # return dict of information when dict() is called
        d = {'mode':self.mode, 'user':self.userN, 'authkey':self.AuthKey}
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
        self.CurrUser = None
