from concurrent.futures import ThreadPoolExecutor, Future
from traceback import format_exc
from fridrich import *
import typing
import socket
import struct
import json
import time
import os


############################################################################
#                             other functions                              #
############################################################################
def json_repair(string: str) -> str:
    """
    if two messages are scrambled together, split them and use the first one
    """
    parts = string.split('}{')  # happens sometimes, probably because python is to slow
    if len(parts) > 1:
        return parts[0]+'}'
    return string


def get_wifi_name() -> str:
    """
    get the name of the wifi currently connected to
    """
    ret = os.popen('Netsh WLAN show interfaces').readlines()   # read interface info
    wifiDict = dict()
    for element in ret:
        tmp = element.split(':')
        if len(tmp) > 1:  # if element is separated with ":" then make it dict
            wifiDict[tmp[0].lstrip().rstrip()] = ':'.join(tmp[1::]).lstrip().rstrip().replace('\n', '')
    
    return wifiDict['SSID']


def date_for_sort(message) -> str:
    """
    go from format "hour:minute:second:millisecond - day.month.year" to "year.month.day - hour:minute:second:millisecond"
    """
    y = message['time'].split(' - ')    # split date and time
    return '.'.join(reversed(y[1].split('.')))+' - '+y[0]   # reverse date and place time at end


def debug(func: typing.Callable) -> typing.Callable:
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)

        except Exception:
            with open("backend.err.log", 'a') as out:
                out.write(format_exc())
            raise
    return wrapper


############################################################################
#                      Server Communication Class                          #
############################################################################
class Connection:
    def __init__(self, debug_mode: str | None = Off, host: str | None = 'fridrich') -> None:
        """
        connect with any fridrich server
        options:
            ``debug_mode`` - ``"normal"`` | ``"full"`` | ``False``
            
            ``host`` - name of the host, either IP or hostname / address
        """
        self.messages = dict()
        self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create socket instance
        self.debug_mode = debug_mode

        sl = host.split('.')
        if len(sl) == 4 and all([digit in '0123456789' for element in sl for digit in element]):
            self.ServerIp = host
        else:
            self.ServerIp = socket.gethostbyname(host)    # get ip of fridrich
        
        if self.debug_mode == 'full':
            print(self.ServerIp)

        if self.debug_mode in ('normal', 'full'):
            print(ConsoleColors.OKGREEN+'Server IP: '+self.ServerIp+ConsoleColors.ENDC)
        self.port = 12345   # set communication port with server

        self.AuthKey = None 
        self.userN = None

        self.loop = True
        
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.receive_thread = Future

    # "local" functions
    @staticmethod
    def error_handler(error: str, *args) -> None:
        """
        Handle incoming errors
        """
        match error:    # match errors where not specific error class exists (and NotEncryptedError)
            case 'NotVoted':
                raise NameError('No votes registered for user')

            case 'json':
                raise JsonError('Crippled message')

            case 'SecurityNotSet':
                raise SecurityClearanceNotSet(args[0]['info'])

            case 'NotEncryptedError':
                raise cryption_tools.NotEncryptedError('Server received non encrypted message')

            case _:  # for all other errors try to raise them and when that fails, raise a ServerError
                if 'full' in args[0] and 'info' in args[0]:
                    st = f'raise {error}("info: {args[0]["info"]} -- Full Traceback: {args[0]["full"]}")'

                elif 'info' in args[0]:
                    st = f'raise {error}("info: {args[0]["info"]}")'

                else:
                    st = f'raise {error}'

                try:
                    exec(st)
                except NameError:
                    raise ServerError(f'{error}:\n{st.lstrip(f"raise {error}(").rstrip(")")}')

    def send(self, dictionary: dict) -> None:
        """
        send messages to server
        """
        if not self.__nonzero__():
            raise AuthError("Not authenticated")

        dictionary['time'] = time.time()

        if self.AuthKey:
            stringMes = json.dumps(dictionary, ensure_ascii=False)
            if any(c in stringMes.lower() for c in ('ö', 'ä', 'ü')):
                raise InvalidRequest('non-ascii charters are not allowed')
            mes = cryption_tools.MesCryp.encrypt(stringMes, key=self.AuthKey.encode())
            self.Server.send(mes)
            if self.debug_mode in ('normal', 'full'):
                print(ConsoleColors.OKCYAN+stringMes+ConsoleColors.ENDC)
            if self.debug_mode == 'full':
                print(ConsoleColors.WARNING+str(mes)+ConsoleColors.ENDC)
            return

        stringMes = json.dumps(dictionary, ensure_ascii=False)
        self.Server.send(cryption_tools.MesCryp.encrypt(stringMes))
        if self.debug_mode in ('normal', 'full'):
            print(ConsoleColors.OKCYAN+stringMes+ConsoleColors.ENDC)

    @debug
    def receive(self):
        """
        receive messages from server, decrypt them and raise incoming errors
        """
        while self.loop:
            try:
                bs = self.Server.recv(8)    # receive message length
                (length,) = struct.unpack('>Q', bs)

            except (ConnectionResetError, struct.error):
                continue

            data = b''
            no_rec = 0
            to_read = 0
            while len(data) < length:   # receive message in patches so size doesn't matter
                o_to_read = to_read
                to_read = length - len(data)
                data += self.Server.recv(
                                    4096 if to_read > 4096 else to_read
                                    )

                if to_read == o_to_read:    # check if new packages were received
                    no_rec += 1
                else:
                    no_rec = 0

                if no_rec >= 100:          # if for 100 loops no packages were received, raise connection loss
                    raise socket.error('Failed receiving data - connection loss')

            try:
                mes = cryption_tools.MesCryp.decrypt(data, self.AuthKey.encode())
            except cryption_tools.InvalidToken:
                self.messages["Error"] = f"cant decrypt: {data}"
                continue

            try:
                mes = json.loads(mes)
            except json.decoder.JSONDecodeError:
                self.messages["Error"] = f"cant decode: {mes}, type: {type(mes)}"
                continue

            try:
                match mes["type"]:
                    case "function":
                        self.messages[mes["time"]] = mes["content"]

                    case "Error":
                        self.messages["Error"] = f"{mes['Error']} - {mes['info']}"

                    case "disconnect":
                        self.messages["disconnect"] = True
                        self.end()

                    case _:
                        raise ServerError(f"server send message: {mes}")

            except KeyError:
                with open("backend.err.log", 'a') as out:
                    out.write(format_exc()+f'message: {mes}')
                raise

    def wait_for_message(self, time_sent: float, timeout: int | None = ..., delay: int | None = .1) -> dict | list:
        """
        wait for the server message to be received.
        :param time_sent: the time the message was sent
        :param timeout: raise a error if no correct message was received (seconds)
        :param delay: The delay for the while loop when checking self.messages
        :return: message(dict)
        """
        start = time.time()
        if self.debug_mode in ('full', 'normal'):
            print(f'waiting for message: {time_sent}')
        while time_sent not in self.messages:  # wait for server message
            if self.debug_mode == 'full':
                print(self.messages)
            if timeout is not ... and time.time()-start >= timeout:
                raise NetworkError("no message was received from server before timeout")
            if "Error" in self.messages:
                raise Error(self.messages["Error"])
            if "disconnect" in self.messages:
                raise ConnectionAbortedError("Server ended connection")
            time.sleep(delay)

        out = self.messages[time_sent]
        del self.messages[time_sent]
        if "Error" in out:
            self.error_handler(out["Error"], out)
        if self.debug_mode in ('all', 'normal'):
            print(f"found message: {out}")
        return out

    def reconnect(self) -> None:
        """
        reconnect to server
        """
        try:    # try to reconnect to the server
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))  # connect to server
        except socket.error:
            raise ConnectionError('Server not reachable')

    # user functions
    def auth(self, username: str, password: str) -> bool:
        """
        authenticate with the server
        """
        if not self.loop:
            raise Error("already called 'end'")
        self.reconnect()

        msg = {  # message
            'type': 'auth',
            'Name': username,
            'pwd': password
        }
        self.userN = username
        self.AuthKey = None  # reset AuthKey
        stringMes = json.dumps(msg, ensure_ascii=False)

        mes = cryption_tools.MesCryp.encrypt(stringMes)
        self.Server.send(mes)

        mes = json.loads(cryption_tools.MesCryp.decrypt(self.Server.recv(2048)))

        self.AuthKey = mes['AuthKey']
        
        self.receive_thread = self.executor.submit(self.receive)  # start thread for receiving
        return mes['Auth']  # return True or False

    def get_sec_clearance(self) -> str:
        """
        if signed in, get security clearance
        """
        msg = {'type': 'secReq', 'time': time.time()}
        self.send(msg)
        
        resp = self.wait_for_message(msg["time"])
        return resp['sec']

    def get_attendants(self, flag: str | None = 'now', voting: str | None = 'GayKing') -> list:
        """
        get Attendants of voting\n
        flag can be "now" or "last"
        """
        msg = {
               'type': 'req',
               'reqType': 'attds',
               'atype': flag, 
               'voting': voting,
               'time': time.time()
        }
        self.send(msg)  # send message
        resp = self.wait_for_message(msg["time"])   # get response

        return resp['Names']    # return names

    def send_vote(self, *args, flag: str | None = 'vote', voting: str | None = 'GayKing') -> None:
        """
        send vote to server\n
        flag can be "vote", "unvote", "dvote" or "dUvote", voting is custom\n
        DoubleVotes are only available once a week\n
        types will be ignored if flag is "dvote"
        """
        msg = {
               'type': flag,
               'voting': voting,
               'time': time.time()
        }
        if flag in ('vote', 'dvote'):
            msg['vote'] = args[0]  # if vote send vote
        
        self.send(msg)  # send vote
        self.wait_for_message(msg["time"])  # receive success or error
    
    def get_results(self, flag: str | None = 'now') -> dict:
        """
        get results of voting\n
        flag can be "now", "last"\n
        return format: {voting : {"totalvotes" : int, "results" : {name1 : votes, name2 : votes}}}
        """
        msg = {
               'type': 'req',
               'reqType': flag,
               'time': time.time()
        }    # set message                    
        self.send(msg)  # send message

        res = self.wait_for_message(msg["time"])    # get response

        out = dict()
        for voting in res:
            attendants = dict()  # create dictionary with all attendants:votes
            nowVoting = res[voting]
            for element in [nowVoting[element] for element in nowVoting]+(['Lukas', 'Niclas', 'Melvin'] if voting == 'GayKing' else []):
                attendants[element] = 0

            votes = int()
            for element in res[voting]:  # assign votes to attendant
                votes += 1
                attendants[res[voting][element]] += 1
            out[voting] = dict()
            out[voting]['totalVotes'] = votes
            out[voting]['results'] = attendants
        
        return out  # return total votes and dict
    
    def get_log(self) -> list:
        """
        get list of recent GayKings
        """
        msg = {
               'type': 'req',
               'reqType': 'log',
               'time': time.time()
        }   # set message
        self.send(msg)  # send request

        res = self.wait_for_message(msg["time"])    # get response
        return res  # return response

    def get_streak(self) -> tuple[str, int]:
        """
        if someone got voted multiple times in a row,\n
        return his/her/their name and how often they\n
        got voted\n
        return format: (Name, Streak)
        """
        log = self.get_log()  # get log dictionary

        sorted_log = {x: log[x] for x in sorted(log, key=lambda x: '.'.join(reversed(x.split('.'))))}    # sort list by year, month, date

        fullList = list(reversed(list(useful.Dict.values(sorted_log))))  # get list of all Kings
        StreakGuys = list(fullList[0].split('|'))   # if a|b|c make list of (a, b, c), else just (a)

        StreakDict = {StreakGuy: int() for StreakGuy in StreakGuys}  # create Dictionary with scheme: {a:0, b:0, c:0}
        for StreakGuy in StreakGuys:    # iterate all guys
            for element in fullList:    # iterate all votes
                if StreakGuy.lower() in element.lower():    # guy was in previous vote
                    StreakDict[StreakGuy] += 1    # add to streak and continue
                else:
                    break   # else begin with new guy

        iDict = useful.Dict.inverse(StreakDict)    # inverse Dict ({1:a, 3:b, 0:c} instead of {a:1, b:3, c:0})
        max_num = max(list(iDict))
        Name = '|'.join([name for name in StreakDict if StreakDict[name] == max_num])
        
        return Name, max_num  # return results

    def get_temps(self) -> tuple[float, float, float]:
        """
        get room and cpu temperature in °C as well as humidity in %
        """
        msg = {
               'type': 'req',
               'reqType': 'temps',
               'time': time.time()
        }  # set message
        self.send(msg)  # send message

        res = self.wait_for_message(msg["time"])    # get response

        return res['Room'], res['CPU'], res['Hum']  # return room and cpu temperature
    
    def get_cal(self) -> dict:
        """
        get Calendar in format {"date":listOfEvents}
        """
        msg = {
               'type': 'req',
               'reqType': 'cal',
               'time': time.time()
        }   # set message
        self.send(msg)  # send request

        res = self.wait_for_message(msg["time"])    # get response
        return res  # return response

    def send_cal(self, date: str, event: str) -> None:
        """
        send entry to calender
        """
        msg = {
               'type': 'CalEntry',
               'date': date,
               'event': event,
               'time': time.time()
        }   # set message
        self.send(msg)  # send message
        self.wait_for_message(msg["time"])  # receive response (success, error)

    def change_pwd(self, new_password: str) -> None:
        """
        Change password of user currently logged in to
        """
        msg = {
               'type': 'changePwd',
               'newPwd': new_password,
               'time': time.time()
        }    # set message
        self.send(msg)  # send message
        self.wait_for_message(msg["time"])  # get response (success, error)

    def get_vote(self, flag: str | None = 'normal', voting: str | None = 'GayKing') -> str:
        """
        get current vote of user\n
        flag can be normal or double
        """
        msg = {
               'type': 'getVote',
               'flag': flag,
               'voting': voting,
               'time': time.time()
        }    # set message
        self.send(msg)  # send request

        resp = self.wait_for_message(msg["time"])   # get response

        return resp['Vote']  # return vote

    def get_version(self) -> str:
        """
        get current version of GUI program
        """
        msg = {
               'type': 'getVersion',
               'time': time.time()
        }  # set message
        self.send(msg)  # send request
        resp = self.wait_for_message(msg["time"])   # get response

        return resp['Version']  # return version

    def set_version(self, version: str) -> None:
        """
        set current version of GUI program
        """
        mes = {
               'type': 'setVersion',
               'version': version,
               'time': time.time()
        }
        self.send(mes)  # send message
        self.receive()  # get response (success, error)

    def get_frees(self) -> int:
        """
        get free double votes
        """
        msg = {
               'type': 'getFrees',
               'time': time.time()
        }
        self.send(msg)
        resp = self.wait_for_message(msg["time"])
        return resp['Value']

    def get_online_users(self) -> list:
        """
        get list of currently online users
        """
        msg = {
               'type': 'gOuser',
               'time': time.time()
        }
        self.send(msg)
        users = self.wait_for_message(msg["time"])['users']
        return users

    def send_chat(self, message: str) -> None:
        """
        send message to chat
        """
        msg = {
               'type': 'appendChat',
               'message': message,
               'time': time.time()
        }
        self.send(msg)
        self.wait_for_message(msg["time"])
    
    def get_chat(self) -> list:
        """
        get list of all chat messages
        """
        msg = {
               'type': 'getChat',
               'time': time.time()
        }
        self.send(msg)
        raw = self.wait_for_message(msg["time"])
        out = sorted(raw, key=date_for_sort)
        return out

    # Admin Functions
    def admin_get_users(self) -> list:
        """
        get list of all users with passwords and security clearance\n
        return format: [{"Name":username, "pwd":password, "sec":clearance}, ...]
        """
        msg = {
               'type': 'getUsers',
               'time': time.time()
        }
        self.send(msg)
        resp = self.wait_for_message(msg["time"])
        return resp
    
    def admin_set_password(self, user: str, password: str) -> None:
        """
        set password of given user
        """
        msg = {
               'type': 'setPwd',
               'User': user,
               'newPwd': password,
               'time': time.time()
        }
        self.send(msg)
        self.wait_for_message(msg["time"])
    
    def admin_set_username(self, old_username: str, new_username: str) -> None:
        """
        change username of given user
        """
        msg = {
               'type': 'setName',
               'OldUser': old_username,
               'NewUser': new_username,
               'time': time.time()
        }
        self.send(msg)
        self.wait_for_message(msg["time"])

    def admin_set_security(self, username: str, password: str) -> None:
        """
        change security clearance of given user
        """
        msg = {
               'type': 'setSec',
               'Name': username,
               'sec': password,
               'time': time.time()
        }
        self.send(msg)
        self.wait_for_message(msg["time"])

    def admin_add_user(self, username: str, password: str, clearance: str) -> None:
        """
        add new user
        """
        msg = {
               'type': 'newUser',
               'Name': username,
               'pwd': password,
               'sec': clearance,
               'time': time.time()
        }
        self.send(msg)
        self.wait_for_message(msg["time"])

    def admin_remove_user(self, username: str) -> None:
        """
        remove user
        """
        msg = {
               'type': 'removeUser',
               'Name': username,
               'time': time.time()
        }
        self.send(msg)
        self.wait_for_message(msg["time"])

    def admin_reset_logins(self) -> None:
        """
        reset all current logins
        """
        msg = {
               'type': 'rsLogins',
               'time': time.time()
        }
        self.send(msg)
        self.wait_for_message(msg["time"])

    # AppStore functions
    def get_apps(self) -> list:
        """
        get all available apps and versions
        """
        msg = {
            "type": "get_apps",
            "time": time.time()
        }
        self.send(msg)
        return self.wait_for_message(msg["time"])

    def download_app(self, app: str) -> None:
        """
        :param app: which app to download
        """
        msg = {
            "type": "download_app",
            "app": app,
            "time": time.time()
        }
        self.send(msg)
        meta = self.wait_for_message(msg["time"])
        data = dict()
        for file in meta:
            data[file] = self.wait_for_message(msg["time"])
        print(meta)
        print(data)
        for file in data:
            with open(meta["filename"], 'w') as out:
                out.write(data[file]["file_content"])

    # magical functions
    def __repr__(self) -> str:
        return f'Backend instance (debug_mode: {self.debug_mode}, user: {self.userN}, authkey: {self.AuthKey})'
    
    def __str__(self) -> str:
        """
        return string of information when str() is called
        """
        return self.__repr__()

    def __iter__(self) -> dict:
        """
        return dict of information when dict() is called
        """
        d = {'debug_mode': self.debug_mode, 'user': self.userN, 'authkey': self.AuthKey}
        for element in d:
            yield element, d[element]

    # def __del__(self):  # end connection if class instance is deleted # caused some issues where it got called without actually calling it
    #     self.end()

    def __nonzero__(self) -> bool:
        """
        return True if AuthKey
        """
        return bool(self.AuthKey)

    def __bool__(self) -> bool:
        """
        return True if AuthKey
        """
        return self.__nonzero__()

    # the end
    def end(self) -> None:
        """
        close connection with server and logout
        """
        msg = {
               'type': 'end',
               'time': time.time()
        }    # set message
        self.send(msg)  # send message
        self.AuthKey = None
        self.userN = None

        self.executor.shutdown(wait=False)
        self.loop = False

        self.executor = ThreadPoolExecutor(max_workers=1)
        self.loop = True
