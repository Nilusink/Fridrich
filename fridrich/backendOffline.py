# to test some functions without the need to be connected to Fridrich
from contextlib import suppress
from datetime import datetime
import time

# local imports
from fridrich.useful import Dict
import fridrich as fr


############################################################################
#                             other functions                              #
############################################################################
def get_wifi_bane():
    return 'Fridrich'


def date_for_sort(message):   # go from format "hour:minute - day.month.year" to "year.month.day - hour:minute"
    y = message['time'].split(' - ')    # split date and time
    return '.'.join(reversed(y[1].split('.')))+' - '+y[0]   # reverse date and place time at end


############################################################################
#                      Server Communication Class                          #
############################################################################
class Connection:
    def __init__(self, debug_mode: str | None = fr.Off, host: str | None = 'fridrich') -> None:
        """
        connect with any fridrich server
        options:
            ``debug_mode`` - ``"normal"`` | ``"full"`` | ``False``

            ``host`` - name of the host, either IP or hostname / address
        """
        self.mode = debug_mode

        self.ServerIp = host
        if self.mode == 'debug':
            print('Server IP: '+self.ServerIp)
        # self.port = 12345   # set communication port with server

        self.AuthKey = None 
        self.yes = {
            'GayKing': {
                'Melvin': 'Hurensohn',
                'Lukas': 'Busfahrer',
                'Niclas': 'SockenTyp'
            }
        }

        self.now = {
            'GayKing': {}
        }

        self.users = [
            'Niclas',
            'Melvin',
            'Lukas'
        ]

        self.dVotes = {user: 1 for user in self.users}

        self.CurrUser = None
        self.log = {
            '20.06.2021': 'Melvin',
            '21.06.2021': 'Lukas|Busfahrer',
            '22.06.2021': 'Niclas|Busfahrer',
            '23.06.2021': 'Melvin|Lukas|Niclas|Busfahrer',
            '24.06.2021': 'Busfahrer',
            '25.06.2021': 'busfahrer',
            '26.06.2021': 'Melvin|Busfahrer',
            '27.06.2021': 'Busfahrer',
            '28.06.2021': 'busfahrer',
            '29.06.2021': 'Busfahrer',
            '30.06.2021': 'Busfahrer',
            '01.07.2021': 'Busfahrer|SockenTyp|jesus',
            '02.07.2021': 'Busfahrer|Melvin'
        }

        self.Calendar = dict()

        self.version = '11.11.11'
        self.chat = list()

    # user functions
    def auth(self, username: str, password: str) -> bool:
        """
        authenticate with the server
        """
        if username in self.users:
            self.CurrUser = username
            return True
        return False

    @staticmethod
    def get_sec_clearance(self) -> str:
        """
        if signed in, get security clearance
        """
        return 'user'

    def get_attendants(self, flag: str | None = 'now', voting: str | None = 'GayKing') -> list:  # flag can be 'now' or 'last'
        """
        get Attendants of voting\n
        flag can be "now" or "last"
        """
        attds = self.users + [element for element in Dict.values(self.now[voting])]

        return attds    # return names

    def send_vote(self, *args, flag: str | None = 'vote', voting: str | None = 'GayKing') -> None:   # flag can be 'vote', 'unvote', 'dvote' or 'dUvote', voting is custom
        """
        send vote to server\n
        flag can be "vote", "unvote", "dvote" or "dUvote", voting is custom\n
        DoubleVotes are only available once a week\n
        types will be ignored if flag is "dvote"
        """
        if not self.CurrUser:
            raise fr.AuthError('Not signed in')
        if flag in ('vote', 'dvote'):
            if voting not in self.now:
                self.now[voting] = dict()
            name = self.CurrUser + ('2' if flag == 'dvote' else '')
            self.now[voting][name] = args[0]
        
        elif flag in ('unvote', 'dUvote'):
            name = self.CurrUser + ('2' if flag == 'dUvote' else '')
            with suppress(KeyError):
                del self.now[voting][name]
        
        else:
            raise fr.InvalidRequest(f'Unknown flag "{flag}"')
    
    def get_results(self, flag: str | None = 'now') -> dict:  # flag can be 'now', 'last', will return Voting:'results':VoteDict and
        """
        get results of voting\n
        flag can be "now", "last"\n
        return format: {voting : {"totalvotes" : int, "results" : {name1 : votes, name2 : votes}}}
        """
        if flag == 'now':
            res = self.now
        elif flag == 'last':
            res = self.yes
        
        else: 
            raise fr.InvalidRequest(f'Unknown flag "{flag}"')

        out = dict()
        for voting in res:
            attds = dict()  # create dictionary with all attendants:votes
            nowVoting = res[voting]
            print(nowVoting)
            for element in [nowVoting[element] for element in nowVoting]+['Lukas', 'Niclas', 'Melvin']:
                attds[element] = 0

            votes = int()
            for element in res[voting]:  # assign votes to attendant
                votes += 1
                attds[res[voting][element]] += 1
            out[voting] = dict()
            out[voting]['totalVotes'] = votes
            out[voting]['results'] = attds
        
        return out  # retur total votes and dict
    
    def get_log(self) -> list:
        """
        get list of recent GayKings
        """
        return self.log

    def get_streak(self) -> tuple[str, int]:
        """
        if someone got voted multiple times in a row,\n
        return his/her/their name and how often they\n
        got voted\n
        return format: (Name, Streak)
        """
        log = self.log  # get log dictionary

        sortedlog = {x: log[x] for x in sorted(log, key=lambda x: '.'.join(reversed(x.split('.'))))}    # sort list by year, month, date

        fullList = list(reversed(list(Dict.values(sortedlog))))  # get list of all Kings
        StreakGuys = list(fullList[0].split('|'))   # if a|b|c make list of (a, b, c), else just (a)

        StreakDict = {StreakGuy: int() for StreakGuy in StreakGuys}  # create Dictionary with scheme: {a:0, b:0, c:0}
        for StreakGuy in StreakGuys:    # iterate all guys
            for element in fullList:    # iterate all votes
                if StreakGuy.lower() in element.lower():    # guy was in previous vote
                    StreakDict[StreakGuy] += 1    # add to streak and continue
                else:
                    break   # else begin with new guy

        iDict = Dict.inverse(StreakDict)    # inversed Dict ({1:a, 3:b, 0:c} instead of {a:1, b:3, c:0})
        Name = iDict[max(iDict)]    # get name of the guy with max streak
        Streak = StreakDict[Name]   # get streak by name
        
        return Name, Streak  # return results

    @staticmethod
    def get_temps(self) -> tuple[float, float, float]:
        """
        get room and cpu temperature in °C as well as humidity in %
        """
        return 26.34, 37.127, 35.98  # return room and cpu temperature
    
    def get_cal(self) -> dict:
        """
        get Calendar in format {"date":listOfEvents}
        """
        return self.Calendar

    def send_cal(self, date: str, event: str) -> None:
        """
        send entry to calender
        """
        if date not in self.Calendar:
            self.Calendar[date] = list()

        self.Calendar[date].append(event)
        
    def change_pwd(self, new_password: str) -> None:
        """
        Change password of user currently logged in to
        """
        return

    def get_vote(self, flag: str | None = 'normal', voting: str | None = 'GayKing') -> str:
        """
        get current vote of user\n
        flag can be normal or double
        """
        if not self.CurrUser:
            raise fr.AuthError('Not signed in')
        user = self.CurrUser + ('2' if flag == 'double' else '')
        try:
            vote = self.now[voting][user]
        except KeyError:
            raise NameError('NotVoted')
        return vote  # return vote

    def get_version(self) -> str:
        """
        get current version of GUI program
        """
        return self.version

    def get_frees(self) -> int:
        """
        get free double votes
        """
        if not self.CurrUser:
            raise fr.AuthError('Not signed in')
        name = self.CurrUser
        return self.dVotes[name]

    def get_online_users(self) -> list:
        """
        get list of currently online users
        """
        if not self.CurrUser:
            raise fr.AuthError('Not sigend in')
        return self.CurrUser

    def send_chat(self, message: str) -> None:
        """
        send message to chat
        """
        curr_time = datetime.now()
        formatted_time = curr_time.strftime('%H:%M:%S.%f')+time.strftime(' - %d.%m.%Y')
        self.chat.append({'time': formatted_time, 'name': self.CurrUser, 'content': message})
    
    def get_chat(self) -> list:
        """
        get list of all chat messages
        """
        out = sorted(self.chat, key=date_for_sort)
        return out

    # some other functions
    def __repr__(self):
        return f'Backend instance (mode: {self.mode}, user: {self.CurrUser}, authkey: {self.AuthKey})'
    
    def __str__(self):  # return string of information when str() is called
        return self.__repr__()

    def __iter__(self):  # return dict of information when dict() is called
        d = {'mode': self.mode, 'user': self.CurrUser, 'authkey': self.AuthKey}
        for element in d:
            yield element, d[element]

    # def __del__(self):  # end connection if class instance is deleted # caused some issues where it got called without actually calling it
    #     self.end()

    def __nonzero__(self):  # return True if AuthKey
        return bool(self.AuthKey)

    def __bool__(self):  # return False if not AuthKey
        return self.__nonzero__()

    # the end
    def end(self):
        self.CurrUser = None
