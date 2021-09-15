#! /usr/bin/python3
from traceback import format_exc
from contextlib import suppress
from threading import Thread
from os import system
import sys

from gpiozero import CPUTemperature

# local imports
from fridrich.cryption_tools import Low, key_func, MesCryp, NotEncryptedError
from fridrich.FanController import CPUHeatHandler
from fridrich.Accounts import Manager
from fridrich.ServerFuncs import *
from fridrich.new_types import *

Const = Constants()
debug = Debug(Const.SerlogFile, Const.errFile)

client: socket.socket


def send_success(cl: socket.socket) -> None:
    """
    send the success message to the client
    """
    Communication.send(cl, {'Success': 'Done'}, encryption=MesCryp.encrypt)
    

def verify(username: str, password: str, cl: socket.socket) -> None:
    """
    verify the client and send result
    """
    global ClientKeys
    resp = AccManager.verify(username, password)
    IsValid = False
    key = None
    if resp is None:
        Communication.send(cl, {'Error': 'SecurityNotSet', 'info': f'no information about security clearance for user {username}'}, encryption=MesCryp.encrypt)
        return

    elif resp:
        IsValid = True
        key = key_func(ClientKeys, length=30)
        ClientKeys[key] = resp
        
    debug.debug(f'Username : {username}'+(' (Bot)' if resp == 'Bot' else '')+', Auth: {IsValid}')   # print out username, if connected successfully or not and if it is a bot
    Communication.send(cl, {'Auth': IsValid, 'AuthKey': key}, encryption=MesCryp.encrypt)    # send result to client


def debug_send_traceback(func: types.FunctionType) -> typing.Callable:
    """
    execute function and send traceback to client
    """
    def wrapper(*args, **kw):
        global client
        try:
            return func(*args, **kw)

        except Exception as ex:
            with suppress(BrokenPipeError):
                error = str(type(ex)).split("'")[1]
                info = str(ex)
                fullTraceback = format_exc()
                with suppress(UnboundLocalError):
                    Communication.send(client, {'Error': error, 'info': info, 'full': fullTraceback})
                with suppress(OSError, AttributeError, UnboundLocalError):
                    client.close()

            debug.debug('Thread 1 error:')
            debug.debug(format_exc())
    return wrapper


@debug_send_traceback
def client_handler() -> None:
    """
    Handles communication with all clients
    """
    global server, reqCounter, ClientKeys, client
    try:
        client, mes = Communication.receive(server, debug.debug, list(ClientKeys))
        if mes is None:
            Communication.send(client, {'Error': 'MessageError', 'info': 'Invalid Message/AuthKey'})
            return

    except NotEncryptedError:
        Communication.send(client, {'Error': 'NotEncryptedError'})
        return

    if mes['type'] == 'auth':   # authorization function
        verify(mes['Name'], mes['pwd'], client)

    elif mes['type'] == 'secReq':
        Communication.send(client, {'sec': ClientKeys[mes['AuthKey']][0]}, encryption=MesCryp.encrypt, key=mes['AuthKey'])

    else:
        if 'AuthKey' not in mes:    # if no AuthKey in message
            debug.debug('auth error, Key not in message')
            Communication.send(client, {'Error': 'AuthError'}, encryption=MesCryp.encrypt)
            client.close()
            return

        else:
            try:
                error, info = FunManager.exec(mes, client)
                fullTraceback = None

            except Exception as ex:
                error = str(type(ex)).split("'")[1]
                info = str(ex)
                fullTraceback = format_exc()

            if error:
                if fullTraceback:
                    print(fullTraceback)
                Communication.send(client, {'Error': error, 'info': info, 'full': fullTraceback})
        
    client.close()  # close so it can be reused


@debug.catch_traceback
def temp_updater(start_time: float) -> None:
    """
    update the temperature
    """
    if time.time()-start_time >= 1:    # every 2 seconds
        start_time += 1
        curr_temp = cpu.temperature
        room_temp, room_hum = read_temp()
        for element in (Const.tempLog, Const.varTempLog):
            with open(element, 'w') as output:
                json.dump({"temp": room_temp, "cptemp": curr_temp, "hum": room_hum}, output)
        time.sleep(.8)


@debug.catch_traceback
def zero_switch(s_time: str | None = '00:00') -> None:
    """
    if time is s_time, execute the switch
    """
    if time.strftime('%H:%M') == s_time:
        with open(Const.lastFile, 'w') as output:    # get newest version of the "votes" dict and write it to the lastFile
            with open(Const.nowFile, 'r') as inp:
                last = inp.read()
                output.write(last)

        Vote.set({'GayKing': {}})
        
        # ---- Log File (only for GayKing Voting)
        last = json.loads(last)['GayKing']  # get last ones

        votes1 = int()
        attds = dict()
        for element in last:    # create a dict with all names and a corresponding value of 0
            attds[last[element]] = 0

        for element in last:    # if name has been voted, add a 1 to its sum
            votes1 += 1
            attds[last[element]] += 1

        highest = str()
        HighestInt = int()
        for element in attds:   # gets the highest of the recently created dict
            if attds[element] > HighestInt:
                HighestInt = attds[element]
                highest = element

            elif attds[element] == HighestInt:
                highest += '|'+element
        
        if HighestInt != 0:
            KingVar[time.strftime('%d.%m.%Y')] = highest
            
            with open(Const.varKingLogFile, 'w') as output:
                output.write(highest)
            
            debug.debug(f"backed up files and logged the GayKing ({time.strftime('%H:%M')})\nGayking: {highest}")
        
        else:
            debug.debug('no votes received')
        if time.strftime('%a') == Const.DoubleVoteResetDay:  # if Monday, reset double votes
            dVotes = DV.value.get()
            for element in dVotes:
                dVotes[element] = Const.DoubleVotes
            DV.value.set(dVotes)

        time.sleep(61)


@debug.catch_traceback
def auto_reboot(r_time: str | None = "03:00") -> None:
    """
    if time is r_time, reboot the server (format is "HH:MM")
    
    if you don't want the server to reboot, just set ``r_time`` to something like "99:99"

    or any other time that will never happen
    """
    if not len(r_time) == 5 and r_time.replace(':', '').isnumeric():
        raise InvalidStringError('r_time needs to be formatted like this: HH:MM')

    if time.strftime('%H:%M') == r_time:
        time.sleep(55)
        system('sudo reboot')


class DoubleVote:
    """
    Handle Double Votes
    """
    def __init__(self, file_path: str) -> None:
        """
        filePath: path to file where double votes are saved
        """
        validUsers = json.loads(Low.decrypt(open(Const.crypFile, 'r').read()))
        self.filePath = file_path

        try:
            value = json.load(open(self.filePath, 'r'))

        except FileNotFoundError:
            value = dict()
            for element in validUsers:
                value[element['Name']] = 1

        self.value = new_types.FileVar(value, self.filePath)

    def vote(self, vote: str, user: str) -> bool:
        """
        if the user has any double votes left,

        vote as "double-user"
        """
        global Vote

        value = self.value.get()
        tmp = Vote.get()
        if user in value:
            if value[user] < 1:
                return False
            try:
                tmp['GayKing'][user+'2'] = vote
            except KeyError:
                tmp['GayKing'] = dict()
                tmp['GayKing'][user+'2'] = vote

            value[user] -= 1
            self.value.set(value)
            Vote.set(tmp)
            return True
        
        value[user] = 0
        self.value.set(value)
        return False

    def unvote(self, user: str, voting: str) -> None:
        """
        unvote DoubleVote
        """
        global Vote
        tmp = Vote.get()
        with suppress(KeyError):
            tmp[voting].pop(user+'2')
        
            value = self.value.get()
            value[user] += 1
            self.value.set(value)
        Vote.set(tmp)

    def get_frees(self, user: str) -> int:
        """
        returns the free double-votes for the given users
        """
        value = self.value.get()
        if user in value:
            return value[user]

        return False


class FunctionManager:
    """
    manages the requested functions
    """
    def __init__(self):
        """
        init switch dict
        """
        self.switch = {
            'admin': {
                'getUsers': AdminFuncs.get_accounts,
                'setPwd': AdminFuncs.set_password,
                'setName': AdminFuncs.set_username,
                'setSec': AdminFuncs.set_security,
                'newUser': AdminFuncs.add_user,
                'removeUser': AdminFuncs.remove_user,
                'end': AdminFuncs.end,
                'rsLogins': AdminFuncs.reset_user_logins,

                'setVersion': ClientFuncs.set_version,
                'getVersion': ClientFuncs.set_version,
                'gOuser': ClientFuncs.get_online_users
            },
            'user': {                                  # instead of 5 billion if'S
                'vote': ClientFuncs.vote,
                'unvote': ClientFuncs.unvote,
                'dvote': ClientFuncs.double_vote,
                'dUvote': ClientFuncs.double_unvote,
                'getVote': ClientFuncs.get_vote,
                'getFrees': ClientFuncs.get_free_votes,
                'CalEntry': ClientFuncs.calendar_handler,
                'req': ClientFuncs.req_handler,
                'end': ClientFuncs.end,
                'changePwd': ClientFuncs.change_pwd,
                'getVersion': ClientFuncs.get_version,
                'gOuser': ClientFuncs.get_online_users,
                'appendChat': ClientFuncs.append_chat,
                'getChat': ClientFuncs.get_chat
            },
            'guest': {                                  # instead of 5 billion if'S
                'CalEntry': ClientFuncs.calendar_handler,
                'getVersion': ClientFuncs.get_version,
                'req': ClientFuncs.req_handler,
                'end': ClientFuncs.end
            },
            'bot': {
                'setVersion': ClientFuncs.set_version,
                'getVersion': ClientFuncs.get_version,
                'end': ClientFuncs.end
            }
        }
    
    def exec(self, message: dict, cl: socket.socket) -> typing.Tuple[bool, typing.Any] | typing.Tuple[str, str]:
        """
        execute the requested function or return error
        """
        clearance = ClientKeys[message['AuthKey']][0]
        if clearance in self.switch:
            if message['type'] in self.switch[clearance]:
                self.switch[clearance][message['type']](message, cl)
                return False, None
            
            else:
                isIn = False
                req = str()
                for element in self.switch:
                    if message['type'] in self.switch[element]:
                        isIn = True
                        req = element
                        break
                
                if isIn:
                    return 'ClearanceIssue', f'Clearance required: "{req}"'
                
                else:
                    return 'InvalidRequest', f'Invalid Request: "{message["type"]}"'

        else:
            return 'ClearanceIssue', f'Clearance not set: "{clearance}"'


class AdminFuncs:
    """
    Manages the Admin Functions
    """
    @staticmethod
    def get_accounts(message: dict, cl: socket.socket, *args) -> None:
        """
        get all users | passwords | clearances
        """
        account_list = AccManager.get_accounts()  # getting and decrypting accounts list
        Communication.send(cl, account_list, encryption=MesCryp.encrypt)  # sending list to client
    
    @staticmethod
    def set_password(message: dict, cl: socket.socket, *args) -> None:
        """
        set a new password for the given user
        """
        AccManager.set_pwd(message['User'], message['newPwd'])   # set new password
        send_success(cl)  # send success

    @staticmethod
    def set_username(message: dict, cl: socket.socket, *args) -> None:
        """
        change the username for the given user
        """
        AccManager.set_username(message['OldUser'], message['NewUser'])  # change account name
        send_success(cl)  # send success
    
    @staticmethod
    def set_security(message: dict, cl: socket.socket, *args) -> None:
        """
        change the clearance for the given user
        """
        AccManager.set_user_sec(message['Name'], message['sec'])
        send_success(cl)

    @staticmethod
    def add_user(message: dict, cl: socket.socket, *args) -> None:
        """
        add a new user with set name, password and clearance
        """
        AccManager.new_user(message['Name'], message['pwd'], message['sec'])
        send_success(cl)
    
    @staticmethod
    def remove_user(message: dict, cl: socket.socket, *args) -> None:
        """
        remove user by username
        """
        AccManager.remove_user(message['Name'])
        send_success(cl)

    @staticmethod
    def reset_user_logins(message: dict, cl: socket.socket, *args) -> None:
        """
        reset all current logins (clear the ClientKeys variable)
        """
        global ClientKeys
        ClientKeys = dict()
        send_success(cl)

    @staticmethod
    def end(message: dict, *args) -> None:
        """
        log-out user
        """
        with suppress(Exception):
            ClientKeys.pop(message['AuthKey'])


class ClientFuncs:
    """
    Manages the Client Functions
    """
    @staticmethod
    def vote(message: dict, cl: socket.socket, *args) -> None:
        """
        vote a name
        
        votes user by username
        """
        global Vote, ClientKeys
        resp = check_if(message['vote'], Vote.get(), message['voting'])
        name = ClientKeys[message['AuthKey']][1]
        
        if not message['voting'] in Vote.get():
            Vote.__setitem__(message['voting'], dict())
            
        tmp = Vote.get()
        tmp[message['voting']][name] = resp
        Vote.set(tmp)    # set vote
        debug.debug(f'got vote: {message["vote"]}                     .')   # print that it received vote (debugging)

        send_success(cl)

    @staticmethod
    def unvote(message: dict, cl: socket.socket, *args) -> None:
        """
        unvote a user
        """
        global Vote
        tmp = Vote.get()
        name = ClientKeys[message['AuthKey']][1]  # WHY U NOT WORKING
        with suppress(KeyError): 
            del tmp[message['voting']][name]  # try to remove vote from client, if client hasn't voted yet, ignore it
        Vote.set(tmp)
        send_success(cl)

    @staticmethod
    def calendar_handler(message: dict, cl: socket.socket, *args) -> None:
        """
        Handle the Calendar requests/write
        """
        calendar = json.load(open(Const.CalFile, 'r'))
        if not message['event'] in calendar[message['date']]:    # if event is not there yet, create it
            try:
                calendar[message['date']].append(message['event'])
            except (KeyError, AttributeError):
                calendar[message['date']] = [message['event']]

            json.dump(calendar, open(Const.CalFile, 'w'))  # update fil
            debug.debug(f'got Calender: {message["date"]} - "{message["event"]}"')    # notify that there has been a calendar entry
        
        send_success(cl)

    @staticmethod
    def req_handler(message: dict, cl: socket.socket, *args) -> None:
        """
        Handle some default requests / logs
        """
        global reqCounter, Vote
        reqCounter += 1
        if message['reqType'] == 'now':   # now is for the current "votes" dictionary
            with open(Const.nowFile, 'r') as inp:
                Communication.send(cl, json.load(inp), encryption=MesCryp.encrypt, key=message['AuthKey'])

        elif message['reqType'] == 'last':  # last is for the "votes" dictionary of the last day
            with open(Const.lastFile, 'r') as inp:
                Communication.send(cl, json.load(inp), encryption=MesCryp.encrypt, key=message['AuthKey'])
                
        elif message['reqType'] == 'log':   # returns the log of the GayKings
            with open(Const.KingFile, 'r') as inp:
                Communication.send(cl, json.load(inp), encryption=MesCryp.encrypt, key=message['AuthKey'])
                
        elif message['reqType'] == 'attds':  # returns All attendants (also non standard users)
            new_ones = get_new_ones(message['atype'], Vote, Const.lastFile, message['voting'])
            Communication.send(cl, {'Names': ['Lukas', 'Niclas', 'Melvin']+new_ones}, encryption=MesCryp.encrypt, key=message['AuthKey'])    # return standard users + new ones
                
        elif message['reqType'] == 'temps':  # returns the temperatures
            r_temp, r_hum = read_temp()
            Communication.send(cl, {'Room': r_temp, 'CPU': currTemp, 'Hum': r_hum}, encryption=MesCryp.encrypt, key=message['AuthKey'])
                
        elif message['reqType'] == 'cal':   # returns the calendar dictionary
            with open(Const.CalFile, 'r') as inp:
                Communication.send(cl, json.load(inp), encryption=MesCryp.encrypt, key=message['AuthKey'])
                
        else:   # notify if an invalid request has been sent
            debug.debug(f'Invalid Request {message["reqType"]}')

    @staticmethod
    def change_pwd(message: dict, cl: socket.socket,  *args) -> None:
        """
        change the password of the user (only for logged in user)
        """
        global ClientKeys
        validUsers = json.loads(cryption_tools.Low.decrypt(open(Const.crypFile, 'r').read()))
        name = ClientKeys[message['AuthKey']][1]
        for element in validUsers:
            if element['Name'] == name:
                element['pwd'] = message['newPwd']
        
        with open(Const.crypFile, 'w') as output:
            fstring = json.dumps(validUsers, ensure_ascii=False)
            c_string = cryption_tools.Low.encrypt(fstring)
            output.write(c_string)
        
        send_success(cl)

    @staticmethod
    def get_vote(message: dict, cl: socket.socket, *args) -> None:
        """
        get the vote of the logged-in user
        """
        if 'flag' in message:
            x = '2' if message['flag'] == 'double' else ''
        else:
            x = ''

        name = ClientKeys[message['AuthKey']][1] + x
        if not message['voting'] in Vote.get():
            Communication.send(cl, {'Error': 'NotVoted'}, encryption=MesCryp.encrypt, key=message['AuthKey'])
            return

        if name not in Vote[message['voting']]:
            Communication.send(cl, {'Error': 'NotVoted'}, encryption=MesCryp.encrypt, key=message['AuthKey'])
            return
        cVote = Vote[message['voting']][name]
        Communication.send(cl, {'Vote': cVote}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    @staticmethod
    def get_version(message: dict, cl: socket.socket, *args) -> None:
        """
        read the Version variable
        """
        vers = open(Const.versFile, 'r').read()
        Communication.send(cl, {'Version': vers}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    @staticmethod
    def set_version(message: dict, cl: socket.socket, *args) -> None:
        """
        set the version variable
        """
        with open(Const.versFile, 'w') as output:
            output.write(message['version'])

        send_success(cl)

    @staticmethod
    def double_vote(message: dict, cl: socket.socket, *args) -> None:
        """
        double vote
        """
        global DV, Vote
        name = ClientKeys[message['AuthKey']][1]
        resp = check_if(message['vote'], Vote.get(), message['voting'])     
        resp = DV.vote(resp, name)
        if resp:
            send_success(cl)
        else:
            Communication.send(cl, {'Error': 'NoVotes'}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    @staticmethod
    def double_unvote(message: dict, cl: socket.socket, *args) -> None:
        """
        double unvote
        """
        global DV
        name = ClientKeys[message['AuthKey']][1]
        DV.unvote(name, message['voting'])
        send_success(cl)

    @staticmethod
    def get_free_votes(message: dict, cl: socket.socket, *args) -> None:
        """
        get free double votes of logged in user
        """
        global DV
        name = ClientKeys[message['AuthKey']][1]
        frees = DV.get_frees(name)

        if frees is False and frees != 0:
            Communication.send(cl, {'Error': 'RegistryError'}, encryption=MesCryp.encrypt, key=message['AuthKey'])
            return
        Communication.send(cl, {'Value': frees}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    @staticmethod
    def get_online_users(message: dict, cl: socket.socket, *args) -> None:
        """
        get all logged in users
        """
        global ClientKeys
        names = list()
        for element in ClientKeys:
            names.append(ClientKeys[element][1])
        
        Communication.send(cl, {'users': names}, encryption=MesCryp.encrypt, key=message['AuthKey'])

    @staticmethod
    def append_chat(message: dict, cl: socket.socket, *args) -> None:
        """
        Add message to chat
        """
        name = ClientKeys[message['AuthKey']][1]
        Chat.add(message['message'], name)
        send_success(cl)

    @staticmethod
    def get_chat(message: dict, cl: socket.socket, *args) -> None:
        """
        get Chat
        """
        resp = Chat.get()
        Communication.send(cl, resp, encryption=MesCryp.encrypt, key=message['AuthKey'])

    @staticmethod
    def end(message: dict, *args) -> None:
        """
        clear logged in user
        """
        global ClientKeys
        with suppress(Exception):
            ClientKeys.pop(message['AuthKey'])


def receive() -> None:
    """
    Basically the whole server
    """
    while not Const.Terminate:
        client_handler()


def update() -> None:
    """
    updates every few seconds
    """
    global currTemp, reqCounter, FanC
    start = time.time()
    start1 = start
    while not Const.Terminate:
        # ----- Temperature updater ------
        temp_updater(start)
        
        # --------  00:00 switch ---------
        zero_switch(Const.switchTime)

        # --------- daily reboot ---------
        auto_reboot(Const.rebootTime)

        # -------- Fan Controller --------
        if time.time()-start1 >= 10:
            start1 += 10
            resp = FanC.iter()
            if resp is not True:
                debug.debug('Fan Controller Error\n'+resp)


############################################################################
#                              Main Program                                #
############################################################################
if __name__ == '__main__':
    client = socket.socket()
    server = socket.socket()
    try:
        reqCounter = 0
        cpu = CPUTemperature()
        currTemp = cpu.temperature

        FanC = CPUHeatHandler()

        ClientKeys = dict()  # list for Client AuthKeys
        
        AccManager = Manager(Const.crypFile)
        FunManager = FunctionManager()

        Vote = FileVar(json.load(open(Const.nowFile, 'r')), (Const.nowFile, Const.varNowFile))
        DV = DoubleVote(Const.doubFile)
        KingVar = FileVar(json.load(open(Const.KingFile, 'r')), (Const.KingFile, Const.varLogFile))

        with open(Const.logFile, 'w') as out:
            out.write('')

        dayRange = 30
        try:
            cal = json.load(open(Const.CalFile, 'r'))
            tod = datetime.datetime.now()
            for i in range(dayRange, 0, -1):
                d = datetime.timedelta(days=i)
                a = tod - d
                dForm = f'{a.day}.{a.month}.{a.year}'
                if dForm not in cal:
                    cal[dForm] = list()
            json.dump(cal, open(Const.CalFile, 'w'))

        except (KeyError, FileNotFoundError):
            cal = dict()
            tod = datetime.datetime.now()
            for i in range(dayRange, 0, -1):
                d = datetime.timedelta(days=i)
                a = tod - d
                dForm = f'{a.day}.{a.month}.{a.year}'
                cal[dForm] = list()
            json.dump(cal, open(Const.CalFile, 'w'))

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((Const.ip, Const.port))
        server.listen()
        debug.debug(Const.ip)

        Updater = Thread(target=update, daemon=True)

        Updater.start()
        
        receive()

    except Exception as e:
        with open(Const.errFile, 'a') as out:   # debug to file because there may be an error before the debug class was initialized
            out.write(f'######## - Exception "{e}" on {datetime.datetime.now().strftime("%H:%M:%S.%f")} - ########\n\n{format_exc()}\n\n######## - END OF EXCEPTION - ########\n\n\n')

        server.shutdown(socket.SHUT_RDWR)
        debug.debug(format_exc())
        Terminate = True
        sys.exit(0)
