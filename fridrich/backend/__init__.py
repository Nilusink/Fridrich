"""
used to interface with a Fridrich Server
(Client)

Author: Nilusink
"""
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Iterable, List, Any, Union
from traceback import format_exc
from contextlib import suppress
from hashlib import sha512
import typing
import socket
import struct
import json
import time
import os

# fridrich imports
from fridrich.file_transfer import send_receive, download_program as now_download_program
from fridrich.file_transfer import download_progress as now_download_progress
from fridrich.backend.debugging import Debugger
from fridrich.classes import Daytime
from fridrich import cryption_tools
from fridrich.errors import *
from fridrich import *


############################################################################
#                     global Variable definition                           #
############################################################################
# Protocol version information
COMM_PROTOCOL_VERSION = "1.1.1"

# debugging
DEBUGGER = Debugger(os.getcwd()+"/logs/fridrich.err", file_mode="a")


############################################################################
#                      Server Communication Class                          #
############################################################################
class FridrichFuture:
    def __init__(self) -> None:
        self.__value: typing.Any | None = ...

    @property
    def result(self) -> typing.Any:
        if self.__value is not ...:
            return self.__value
        raise ValueError("No value received yet")

    @result.setter
    def result(self, value) -> None:
        self.__value = value

    def __repr__(self) -> str:
        return f"<future: result={self.__value is not ...}>"

    def __bool__(self) -> bool:
        """
        return True if AuthKey
        """
        return self.__value is not ...


class Connection:
    def __init__(self, debug_mode: str | None = False, host: str | None = ...) -> None:
        """
        connect with any fridrich server

        :param debug_mode: "normal" | "full" | False
        :param host: name of the host, either IP or hostname / address
        """
        self._messages = dict()
        self._server_messages = dict()
        self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create socket instance
        self._debug_mode = debug_mode

        self.__ServerIp = None

        if host is not ...:
            self.server_ip = host

        if self._debug_mode in ('normal', 'full'):
            print(ConsoleColors.OKGREEN + 'Server IP: ' + self.server_ip + ConsoleColors.ENDC)
        self.port = 12345   # set communication port with server

        self.__AuthKey = None
        self.__userN = None
        self.__pwd_hash = None

        self.loop = True

        self.executor = ThreadPoolExecutor(max_workers=1)
        self.receive_thread = Future()

        # for down-/uploading
        self.load_state = str()
        self.load_progress = float()
        self.load_program = str()

        # message pool
        self.__message_pool: list = []
        self.__results_getters: Dict[str, FridrichFuture] = {}

        # optimization variables
        self.__server_time_delta = None
        self.__server_voting_time = None

        self.__login_time = None

    # properties
    @property
    def username(self) -> str:
        """
        get username
        """
        return self.__userN

    @property
    def server_ip(self) -> str:
        return self.__ServerIp

    @server_ip.setter
    def server_ip(self, value: str) -> None:
        sl = value.split('.')
        if len(sl) == 4 and all([digit in '0123456789' for element in sl for digit in element]):
            if self._debug_mode in ("full", "normal"):
                try:
                    socket.gethostbyaddr(value)
                except socket.herror:
                    print(ConsoleColors.WARNING+f"Hostname of {value} not found, may be unreachable"+ConsoleColors.ENDC)
            self.__ServerIp = value
        else:
            self.__ServerIp = socket.gethostbyname(value)  # get ip of fridrich

        if self._debug_mode == 'full':
            print(self.server_ip)

    @property
    def debug_mode(self) -> str:
        return self._debug_mode

    @debug_mode.setter
    def debug_mode(self, value: str) -> None:
        allowed = ("normal", "full", False)
        if value not in allowed:
            raise ValueError(f"must be {' or '.join([str(el) for el in allowed])}")
        self._debug_mode = value

    @property
    def login_time(self) -> Daytime | None:
        return self.__login_time

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
                    st = f'raise {error}("{args[0]["info"]} -- Full Traceback: {args[0]["full"]}")'

                elif 'info' in args[0]:
                    st = f'raise {error}("{args[0]["info"]}")'

                else:
                    st = f'raise {error}'

                try:
                    exec(st)

                except NameError:
                    raise ServerError(f'{error}:\n{st.lstrip(f"raise {error}(").rstrip(")")}')

    @DEBUGGER.catch_and_write(raise_error=True, print_traceback=True)
    def response_handler(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """
        if necessary, process each result
        """
        if self._debug_mode == "full":
            print(f"handling responses {responses=}")
        for response in responses.keys():
            match response:
                case "getFrees":
                    responses[response] = responses[response]['Value']

                case "getChat":
                    raw = responses[response]
                    responses[response] = sorted(raw, key=date_for_sort)

                case "get_var":
                    responses[response] = responses[response]["var"]

                case "ping":
                    responses[response] = (time.time() - responses["ping"]["time"]) * 1000

                case "get_time":
                    self.__server_voting_time = Daytime.from_strftime(responses[response]["voting"])
                    responses[response]["voting"] = self.__server_voting_time
                    responses[response]["now"] = Daytime.from_strftime(responses[response]["now"])

                    lo_now = Daytime.now()
                    tmp = abs(lo_now - responses[response]["now"])
                    if tmp > 0:
                        tmp = (3600*24) - tmp

                    self.__server_time_delta = Daytime.from_abs(tmp)

                    responses[response]["difference"] = self.__server_time_delta
                    responses[response]["until_voting"] = self.__server_voting_time - responses[response]["now"]

                case _:
                    if response.startswith("gRes"):  # because it could also be "gRes|last" or "gRes+now"
                        res = responses[response]
                        out = dict()

                        for voting in res:
                            attendants = dict()  # create dictionary with all attendants: votes
                            now_voting = res[voting]
                            everyone = [now_voting[element] for element in now_voting]
                            everyone += (['Lukas', 'Niclas', 'Melvin'] if voting == 'GayKing' else [])
                            for element in everyone:
                                attendants[element] = 0

                            votes = int()
                            for element in res[voting]:  # assign votes to attendant
                                votes += 1
                                attendants[res[voting][element]] += 1
                            out[voting] = dict()
                            out[voting]['totalVotes'] = votes
                            out[voting]['results'] = attendants

                        responses[response] = out

        return responses

    def _send(self, dictionary: dict, wait: bool = False) -> float | None:
        """
        send messages to server

        :param dictionary: dict to send
        :param wait: don't send the messages immediately and wait
        :return: time of sending
        """
        if not self:
            raise AuthError("Cannot send message - not authenticated yet!")
        self.__message_pool.append(dictionary)
        if not wait:
            return self.__send()

    def __send(self) -> float:
        """
        the actual sending process
        """
        # check errors before executing
        if not self.server_ip:
            raise Error("no host set")

        if not self.__bool__():
            raise AuthError("Not authenticated")

        if len(self.__message_pool) == 0:
            raise ValueError("Client: Message Pool Empty")

        for element in self.__message_pool:
            if "message" in element:
                element["message"] = element["message"].replace("'", "\'").replace('"', '\"')

        message = {
            "time": time.time(),
            "content": self.__message_pool
        }

        if self.__AuthKey:
            string_mes = json.dumps(message, ensure_ascii=True)
            mes = cryption_tools.MesCryp.encrypt(string_mes, key=self.__AuthKey.encode())

            try:
                self.Server.send(mes)
                # reset message pool only if the message was sent successfully
                self.__message_pool = []

            except BrokenPipeError:
                self.end(revive=True)
                return -1

            if self._debug_mode in ('normal', 'full'):
                print(ConsoleColors.OKCYAN+string_mes+ConsoleColors.ENDC)
            if self._debug_mode == 'full':
                print(ConsoleColors.WARNING+str(mes)+ConsoleColors.ENDC)

            return message["time"]

        string_mes = json.dumps(message, ensure_ascii=False)
        self.Server.send(cryption_tools.MesCryp.encrypt(string_mes))

        # reset message pool only if the message was sent successfully
        self.__message_pool = []
        if self._debug_mode in ('normal', 'full'):
            print(ConsoleColors.OKCYAN+string_mes+ConsoleColors.ENDC)

        return message["time"]

    def send(self) -> dict:
        """
        send the messages and also receive them
        """
        res = self.wait_for_message(self.__send())
        return res

    def __assign_results(self, results: dict) -> None:
        if self._debug_mode in ("normal", "full"):
            print(f"assigning {results=}")

        if results is ...:
            raise ValueError("results not set")

        for element in results.keys():
            # check if the element is in both list (using sets)
            if not set(results.keys()) & set(self.__results_getters.keys()) & {element}:
                raise ValueError(f"element {element} not in results and getters")

            if self._debug_mode == "full":
                print(f"appended {element=}, now: {self.results_getters}")
            self.__results_getters[element].result = results[element]

        for element in set(self.__results_getters.keys()) - set(results.keys()):
            self.__results_getters[element].result = False

    @property
    def results_getters(self) -> dict:
        return self.__results_getters

    @DEBUGGER.catch_and_write(raise_error=True, print_traceback=True)
    def receive(self):
        """
        receive messages from server, decrypt them and raise incoming errors (meant as thread, run by default)
        """
        while self.loop:
            try:
                bs = self.Server.recv(8)    # receive message length
                (length,) = struct.unpack('>Q', bs)

            except (ConnectionResetError, struct.error, socket.timeout):
                continue
            if self._debug_mode == "full":
                print(f"new message, receiving now")

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

            if self._debug_mode == "full":
                print("received data")

            try:
                mes = cryption_tools.MesCryp.decrypt(data, self.__AuthKey.encode())
            except cryption_tools.InvalidToken:
                self._messages["Error"] = {"Error": "MessageError", "info": f"cant decrypt: {data}"}
                continue

            if self._debug_mode in ("full", "normal"):
                print(f"decrypted data: {mes=}")

            try:
                for _ in range(2):
                    mes = mes.replace("\\\\", "\\")
                mes = json.loads(mes)

            except json.decoder.JSONDecodeError:
                self._messages["Error"] = f"cant decode: {mes}, type: {type(mes)}"
                continue

            try:
                # parse each message
                for resp_type, message in mes["content"].items():
                    match message["type"]:
                        case "function":
                            if mes["time"] not in self._messages:
                                self._messages[mes["time"]] = {}

                            self._messages[mes["time"]][resp_type] = message["content"]

                        case "Error":
                            self._messages["Error"] = message["content"]

                        case "disconnect":
                            self._messages["disconnect"] = True
                            self.end()

                        case "ServerRequest":
                            self._server_messages[mes['time']] = message

                        case _:
                            raise ServerError(f"server send message: {mes}")

            except KeyError:
                with open("backend.err.log", 'a') as out:
                    out.write(format_exc()+f'message: {mes}')
                raise

    def wait_for_message(self, time_sent: float, timeout: int | bool | None = 10, delay: int | None = .1) -> dict:
        """
        wait for the server message to be received.
        :param time_sent: the time the message was sent
        :param timeout: raise an error if no correct message was received (seconds)
        :param delay: The delay for the while loop when checking self.messages
        :return: message(dict)
        """
        start = time.time()
        if self._debug_mode in ('full', 'normal'):
            print(f'waiting for message: {time_sent}')

        while time_sent not in self._messages:  # wait for server message
            if self._debug_mode == 'full':
                print(self._messages)

            if timeout and time.time()-start >= timeout:
                raise NetworkError("no message was received from server before timeout")

            elif "Error" in self._messages:
                for _ in range(10):
                    if time_sent in self._messages:
                        break
                    time.sleep(.01)
                break

            elif "disconnect" in self._messages:
                raise ConnectionAbortedError("Server ended connection")
            time.sleep(delay)

        with suppress(KeyError):
            out = self._messages[time_sent]
            del self._messages[time_sent]

            if len(out) == 0:
                raise MessageError("received empty message pool from server")

            out = self.response_handler(out)
            self.__assign_results(out)

        if "Error" in self._messages:
            try:
                error_name, full_error = self._messages["Error"]["Error"],  self._messages["Error"]

            except TypeError:
                raise Error(self._messages.pop("Error"))

            self._messages.pop("Error")
            self.error_handler(error_name, full_error)
            return {}

        if self._debug_mode in ('all', 'normal'):
            print(f"found message: {out}")

        return out

    def reconnect(self) -> None:
        """
        reconnect to server
        """
        try:    # try to reconnect to the server
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.server_ip, self.port))  # connect to server
        except socket.error:
            raise ConnectionError('Server not reachable')

    # user functions
    def auth(self, username: str, password: str, pwd_hashed: bool = False) -> bool:
        """
        authenticate with the server
        """
        if not self.server_ip:
            raise Error("no host set")

        if not self.loop:
            raise Error("already called 'end'")

        if self:
            self.end(revive=True)

        self.reconnect()
        msg = {  # message
            'type': 'auth',
            'Name': username,
            'pwd': sha512(password.encode()).hexdigest() if not pwd_hashed else password,
            "com_protocol_version": COMM_PROTOCOL_VERSION
        }
        self.__userN = username
        self.__pwd_hash = msg["pwd"]
        self.__AuthKey = None  # reset AuthKey
        string_mes = json.dumps(msg, ensure_ascii=False)

        mes = cryption_tools.MesCryp.encrypt(string_mes)
        self.Server.send(mes)

        mes = json.loads(cryption_tools.MesCryp.decrypt(self.Server.recv(2048)))
        if "Error" in mes:
            self.error_handler(mes["Error"], mes)
        self.__AuthKey = mes['AuthKey']

        # setting timeout for receive thread
        self.Server.settimeout(.5)

        self.receive_thread = self.executor.submit(self.receive)  # start thread for receiving
        if mes["Auth"]:
            self.__login_time = Daytime.now()

        return mes['Auth']  # return True or False

    def re_auth(self) -> bool:
        """
        if a user has already been logged in, you can now try to re-login
        """
        if self.__userN is None or self.__pwd_hash is None:
            return False

        self.end(revive=True)
        return self.auth(username=self.__userN, password=self.__pwd_hash, pwd_hashed=True)

    def get_sec_clearance(self, wait: bool = False) -> str | FridrichFuture:
        """
        if signed in, get security clearance
        """
        msg = {'type': 'secReq'}

        self._send(msg, wait=True)

        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def send_vote(self, *args, flag: str | None = 'vote', voting: str | None = 'GayKing', wait: bool = False) -> None:
        """
        send vote to server\n
        flag can be "vote", "unvote", "dvote" or "dUvote", voting is custom\n
        DoubleVotes are only available once a week\n
        types will be ignored if flag is "dvote"
        """
        msg = {
               'type': flag,
               'voting': voting
        }
        if flag in ('vote', 'dvote'):
            msg['vote'] = args[0]  # if vote send vote

        self._send(msg, wait=True)

        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def get_results(self, flag: str | None = 'now', wait: bool = False) -> dict | FridrichFuture:
        """
        get results of voting\n
        flag can be "now", "last"\n
        return format: {voting : {"totalvotes" : int, "results" : {name1 : votes, name2 : votes}}}
        """
        msg = {
               'type': 'gRes',
               'flag': flag,
               'f_name': "gRes"+flag
        }    # set message
        self._send(msg, wait=True)

        res = FridrichFuture()
        self.__results_getters[msg["f_name"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def get_log(self, wait: bool = False) -> dict | FridrichFuture:
        """
        get list of recent GayKings
        """
        msg = {
               'type': 'gLog'
        }   # set message
        self._send(msg, wait=True)

        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    @staticmethod
    def calculate_streak(log: dict) -> tuple[str, int]:
        """
        if someone got voted multiple times in a row,
        return their name and how often they
        got voted
        :return: (Name, Streak)
        """
        # sort list by year, month, date
        sorted_log = {x: log[x] for x in sorted(log, key=lambda x: '.'.join(reversed(x.split('.'))))}
        try:
            streak_guys: dict = {guy: 0 for guy in sorted_log[list(sorted_log.keys())[-1]].split("|")}
        except AttributeError:
            raise ValueError("Please only pass one voting per time")

        for guy in streak_guys.keys():
            for date in reversed(sorted_log.keys()):
                if guy in sorted_log[date] and streak_guys[guy] != -1:
                    streak_guys[guy] += 1
                    continue
                break

        max_num = max(list(streak_guys.values()))
        names = "|".join([guy for guy in streak_guys if streak_guys[guy] == max_num])
        return names, max_num  # return results

    def get_cal(self, wait: bool = False) -> dict | FridrichFuture:
        """
        get Calendar in format {"date":listOfEvents}
        """
        msg = {
               'type': 'gCal'
        }   # set message
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def send_cal(self, date: str, event: str, wait: bool = False) -> None:
        """
        send entry to calender
        """
        msg = {
               'type': 'CalEntry',
               'date': date,
               'event': event
        }   # set message
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def change_pwd(self, new_password: str, wait: bool = False) -> None:
        """
        Change password of user currently logged in to
        """
        msg = {
               'type': 'changePwd',
               'newPwd': sha512(new_password.encode()).hexdigest()
        }    # set message
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def get_vote(self, flag: str | None = 'normal', voting: str | None = 'GayKing',
                 wait: bool = False) -> str | FridrichFuture:
        """
        get current vote of user\n
        flag can be normal or double
        """
        msg = {
               'type': 'getVote',
               'flag': flag,
               'voting': voting,
               'f_name': "getVote"+flag
        }    # set message
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["f_name"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def get_version(self, wait: bool = False) -> str | FridrichFuture:
        """
        get current version of GUI program
        """
        msg = {
               'type': 'getVersion'
        }  # set message
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def set_version(self, version: str, wait: bool = False) -> None:
        """
        set current version of GUI program
        """
        msg = {
               'type': 'setVersion',
               'version': version
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def get_frees(self, wait: bool = False) -> int | FridrichFuture:
        """
        get free double votes
        """
        msg = {
               'type': 'getFrees'
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def get_online_users(self, wait: bool = False) -> list | FridrichFuture:
        """
        get list of currently online users
        """
        msg = {
               'type': 'gOuser'
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def send_chat(self, message: str, wait: bool = False) -> None:
        """
        send message to chat
        """
        msg = {
               'type': 'appendChat',
               'message': message
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def get_chat(self, wait: bool = False) -> list | FridrichFuture:
        """
        get list of all chat messages
        """
        msg = {
               'type': 'getChat'
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def get_weather_stations(self, wait: bool = False) -> List[Dict[str, str]] | FridrichFuture:
        """
        get the names and locations of all registered weather stations
        """
        msg = {
            "type": "get_stations"
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def get_temps_now(self, wait: bool = False) -> dict | FridrichFuture:
        msg = {
            "type": "get_temps_now"
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def get_temps_log(self, station_name: str, wait: bool = False) -> dict | FridrichFuture:
        msg = {
            "type": "get_temps_log",
            "station_name": station_name
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    # user controlled variables:
    def get_all_vars(self, wait: bool = False) -> dict | FridrichFuture:
        """
        get all user controlled variables inside a dict
        """
        msg = {
            "type": "get_all_vars"
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def get_var(self, variable: str, wait: bool = False) -> Any | FridrichFuture:
        """
        get a user controlled variable
        """
        msg = {
            "type": "get_var",
            "var": variable
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def set_var(self, variable: str, value, wait: bool = False) -> None:
        """
        set a user controlled variable
        must be json valid!
        """
        msg = {
            "type": "set_var",
            "var": variable,
            "value": value
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def del_var(self, variable: str, wait: bool = False) -> None:
        """
        delete a user controlled variable
        """
        msg = {
            "type": "del_var",
            "var": variable
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def __iter__(self) -> Iterable:
        """
        return dict of all User Controlled Variables when called
        """
        _d = self.get_all_vars()
        for element in _d:
            yield element, _d[element]

    def __getitem__(self, item: str):
        return self.get_var(item)

    def __setitem__(self, key: str, value) -> None:
        return self.set_var(key, value)

    def __delitem__(self, item: str) -> None:
        return self.del_var(item)

    # WeatherStation Funcs
    def register_station(self, station_name: str, location: str, wait: bool = False) -> Union[FridrichFuture, None]:
        """
        register a new weather station
        """
        msg = {
            "type": "register",
            "station_name": station_name,
            "location": location
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def commit_weather_data(self, station_name: str, weather_data: dict,
                            wait: bool = False, set_time: str | None = ...) -> Union[None, FridrichFuture]:
        """
        Commit data to the WeatherStation database
        """
        msg = {
            "type": "commit",
            "time": time.strftime("%Y.%m.%d")+"-"+Daytime.now().to_string() if set_time is ... else set_time,
            "station_name": station_name
        }
        msg.update(weather_data)
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    # Admin Functions
    def admin_get_users(self, wait: bool = False) -> list | FridrichFuture:
        """
        get list of all users with passwords and security clearance\n
        return format: [{"Name":username, "pwd":password, "sec":clearance}, ...]
        """
        msg = {
               'type': 'getUsers'
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def admin_set_password(self, user: str, password: str, wait: bool = False) -> None:
        """
        set password of given user
        """
        msg = {
               'type': 'setPwd',
               'User': user,
               'newPwd': sha512(password.encode()).hexdigest()
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def admin_set_username(self, old_username: str, new_username: str, wait: bool = False) -> None:
        """
        change username of given user
        """
        msg = {
               'type': 'setName',
               'OldUser': old_username,
               'NewUser': new_username
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def admin_set_security(self, username: str, password: str, wait: bool = False) -> None:
        """
        change security clearance of given user
        """
        msg = {
               'type': 'setSec',
               'Name': username,
               'sec': password
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def admin_add_user(self, username: str, password: str, clearance: str, wait: bool = False) -> None:
        """
        add new user
        """
        msg = {
               'type': 'newUser',
               'Name': username,
               'pwd': sha512(password.encode()).hexdigest(),
               'sec': clearance
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def admin_remove_user(self, username: str, wait: bool = False) -> None:
        """
        remove user
        """
        msg = {
               'type': 'removeUser',
               'Name': username
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def admin_reset_logins(self, wait: bool = False) -> None:
        """
        reset all current logins
        """
        msg = {
               'type': 'rsLogins'
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def manual_voting(self, wait: bool = False) -> None:
        """
        trigger a voting manually
        """
        msg = {
            "type": "trigger_voting"
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    def kick_user(self, user_to_kick: str, wait: bool = False) -> None:
        """
        kick one user by its username
        """
        msg = {
            "type": "kick_user",
            "user": user_to_kick
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()

    # AppStore functions
    def get_apps(self, wait: bool = False) -> list | FridrichFuture:
        """
        get all available apps and versions
        """
        msg = {
            "type": "get_apps"
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def download_app(self, app: str, directory: str | None = ...) -> None:
        """
        :param app: which app to download
        :param directory: where the program should be downloaded to
        """
        msg = {
            "type": "download_app",
            "app": app
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        self.send()
        meta = res.result

        self.load_state = "Uploading"
        for _ in meta:
            thread = send_receive(mode='receive', print_steps=False, download_directory=directory, thread=True,
                                  overwrite=True)
            while thread.running():
                pass
                self.load_program = now_download_program
                self.load_progress = now_download_progress
        self.load_state = str()
        self.load_program = str()
        self.load_progress = float()

    def _send_app(self, files: list | tuple, app_name: str) -> None:
        for file in files:
            thread = send_receive(mode="send", filename=file, destination=self.server_ip, print_steps=False,
                                  thread=True, overwrite=True)
            while thread.running():
                self.load_program = app_name
        self.load_program = str()
        self.load_state = str()

    def create_app(self, app_name: str, app_version: str, app_info: str, files: list | tuple) -> None:
        """
        add a new app to the fridrich appstore
        """
        msg = {
            "type": "create_app",
            "name": app_name,
            "version": app_version,
            "info": app_info,
            "files": [file.split("/")[-1] for file in files]
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        self.send()

        self.load_state = "Uploading"
        self._send_app(files, app_name)

    def modify_app(self, old_app_name: str, app_name: str, app_version: str, app_info: str,
                   files: list | tuple, to_delete: list | tuple) -> None:
        """
        configure an already existing app

        :param old_app_name: the original name of the app
        :param app_name: the name of the app
        :param app_version: the version of the app
        :param app_info: the info of the app
        :param files: a list with files to update (full path, overwriting old files)
        :param to_delete: a list with App-Files that should be deleted (if the app exist!)
        """
        msg = {
            "type": "modify_app",
            "o_name": old_app_name,
            "name": app_name,
            "version": app_version,
            "info": app_info,
            "files": [file.split("/")[-1].split("\\")[-1] for file in files],
            "to_remove": to_delete
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        self.send()

        self._send_app(files, app_name)

    # tools
    def ping(self, wait: bool = False) -> float | FridrichFuture:
        """
        ping the server to check the connection time
        :return: time in ms
        """
        msg = {
            "type": "ping",
            "time": time.time()
        }
        self._send(msg, wait=True)

        # result handling
        res = FridrichFuture()
        self.__results_getters[msg["type"]] = res
        if not wait:
            self.send()
            return res.result
        return res

    def get_server_time(self, wait: bool = False, reload: bool = False) -> dict | FridrichFuture:
        """
        get the current server time and voting time
        :param reload: if already called once and False, doesn't request new time from server (local update)
        :param wait: if reload is set, sets if waits for Connection.send()
        """
        res = FridrichFuture()
        if not self.__server_time_delta or reload:
            msg = {
                "type": "get_time"
            }
            self._send(msg, wait=True)

            # result handling
            self.__results_getters[msg["type"]] = res
            if not wait:
                self.send()
                return res.result
            return res

        tmp = Daytime.now() + self.__server_time_delta
        res.result = {
            "now": tmp,
            "voting": self.__server_voting_time,
            "difference": self.__server_time_delta,
            "until_voting": self.__server_voting_time - tmp
        }
        if not wait:
            return res.result
        return res

    # magical functions
    def __repr__(self) -> str:
        return f'<Backend instance (debug_mode: {self._debug_mode}, user: {self.__userN})>'

    def __str__(self) -> str:
        """
        return string of information when str() is called
        """
        return self.__repr__()

    def __bool__(self) -> bool:
        """
        return True if AuthKey
        """
        return bool(self.__AuthKey)

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, exception_type, value, traceback) -> bool:
        self.end(revive=False)
        if exception_type is not None:
            return False
        return True

    def __del__(self) -> None:
        self.end(revive=False)

    def __eq__(self, other: "Connection") -> bool:
        if not type(other) == Connection:
            return self.__bool__()

        return all([str(self) == str(other), bool(self) is bool(other), self.server_ip == other.server_ip,
                    self.port == other.port])

    # the end
    def end(self, revive: bool = False) -> None:
        """
        close connection with server and logout
        """
        msg = {
               'type': 'end'
        }    # set message
        with suppress(ConnectionResetError, ConnectionAbortedError, AuthError):
            self._send(msg, wait=False)  # send message

        self.loop = False
        self.__AuthKey = None
        self.__login_time = None

        if revive:
            # waiting for receive thread to shut down
            while not self.receive_thread.done():
                time.sleep(.1)

            # re-creating the thread-pool
            del self.executor
            self.executor = ThreadPoolExecutor(max_workers=1)
            self.loop = True
            return

        self.executor.shutdown(wait=True)
        # app_store.executor.shutdown(wait=False)


############################################################################
#                             helper functions                             #
############################################################################
def date_for_sort(message: dict) -> str:
    """
    go from format
    "hour:minute:second:millisecond - day.month.year" to "year.month.day - hour:minute:second:millisecond"
    """
    y = message['time'].split(' - ')    # split date and time
    return '.'.join(reversed(y[1].split('.')))+' - '+y[0]   # reverse date and place time at end
