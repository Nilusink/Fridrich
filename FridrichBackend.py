from contextlib import suppress
from wolframalpha import Client
import err_classes as err
import socket, json

############################################################################
#                      Server Communication Class                          #
############################################################################
class Connection:
    def __init__(self):
        self.ServerIp = socket.gethostbyname('Fridrich')
        print('Server IP: '+self.ServerIp)
        self.port = 12345

        self.AuthKey = None

    def errorHandler(self, error):
        if error == 'AccessError':
            raise err.AccessError('Access denied')
        
        elif error == 'AuthError':
            raise err.AuthError('Authentification failed')
        
        elif error == 'NotVoted':
            raise NameError('Not Voted')
        
        elif error == 'json':
            raise err.JsonError('Crypled message')

    def send(self, dictionary):
        dictionary['AuthKey'] = self.AuthKey
        msg = json.dumps(dictionary).encode('utf-8')
        self.Server.send(msg)

    def recieve(self, length=1024):
        msg = self.Server.recv(length).decode('utf-8')
        try:
            msg = json.loads(msg)
        except json.JSONDecodeError:
            self.errorHandler('json')

        if 'Error' in msg:
            success = False
        else:
            success = True

        if success:
            return msg
        print('Error:')
        print(msg['Error'])
        
        self.errorHandler(msg['Error'])

    def auth(self, username:str, password:str):
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError

        msg = json.dumps({
            'type':'auth',
            'Name':username,
            'pwd':password
        })
        self.Server.send(msg.encode('utf-8'))
        resp = json.loads(self.Server.recv(1024).decode('utf-8'))

        self.AuthKey = resp['AuthKey']

        return resp['Auth']

    def getAttendants(self, flag = 'now'): # flag can be 'now' or 'last'
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError

        self.send({'type':'req', 'reqType':'attds', 'atype':flag})
        resp = self.recieve()

        return resp['Names']

    def sendVote(self, *args, flag = 'vote'): # flag can be 'vote' or 'unvote'
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError

        if flag == 'vote':
            msg = {'type':flag, 'vote':args[0]}
        else:
            msg = {'type':flag}
        
        self.send(msg)
        self.recieve()
    
    def getResults(self, flag = 'now'): # flag can be 'now', 'last'
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError

        msg = {'type':'req', 'reqType':flag}
        self.send(msg)

        res = self.recieve()

        attds = dict()
        for element in [res[element] for element in res]+['Lukas', 'Niclas', 'Melvin']:
            attds[element] = int()

        votes = int()
        for element in res:
            votes+=1
            attds[res[element]]+=1
        
        return votes, attds
    
    def getLog(self):
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError

        msg = {'type':'req', 'reqType':'log'}
        self.send(msg)

        res = self.recieve()
        return res
    
    def getTemps(self):
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError

        msg = {'type':'req', 'reqType':'temps'}
        self.send(msg)

        res = self.recieve()

        return res['Room'], res['CPU']
    
    def getCal(self):
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError

        msg = {'type':'req', 'reqType':'cal'}
        self.send(msg)

        res = self.recieve()
        return res

    def sendCal(self, date:str, event:str):
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError

        msg = {'type':'CalEntry', 'date':date, 'event':event}
        self.send(msg)

    def changePwd(self, newPassword:str):
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError
        
        mes = {'type':'changePwd', 'newPwd':newPassword}
        self.send(mes)

    def getVote(self):
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError
        
        mes = {'type':'getVote'}
        self.send(mes)

        resp = self.recieve()

        return resp['Vote']

    def end(self):
        try:
            self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Server.connect((self.ServerIp, self.port))
        except socket.error:
            raise ValueError
        
        msg = {'type':'end'}
        self.send(msg)

############################################################################
#                   Class for Searching Wolfram Alpha                      #
############################################################################
class wiki:
    def __init__(self):
        # App id obtained by the above steps
        app_id = 'U3ETL7-RL45EG5R6Y'
        # Instance of wolf ram alpha 
        # client class
        self.client = Client(app_id)
    
    def getInfos(self, keyword):
        # Stores the response from 
        # wolf ram alpha
        res = self.client.query(keyword)
        resDict = dict()
        if res['@success']:
            for element in res['pod']:
                t = element['@title']
                with suppress(TypeError):
                    resDict[t] = element['subpod']['plaintext']
        return resDict

if __name__ == '__main__':
    from traceback import format_exc    # imports for shell

    c = Connection()    # create connection instance
    w = wiki()  # create wiki instance
    print('initialised Connections')

    print('\n\nfunctions of Connection: ')  #return all functions of the two classes
    funcs = dir(Connection)
    for element in funcs:
        if not element.startswith('__'):
            print('  - '+element)
    
    print('\nfunctions of wiki: ')
    funcs = dir(wiki)
    for element in funcs:
        if not element.startswith('__'):
            print('  - '+element)
    print()

    while True: # shell for debugging
        try:
            cmd = input('>> ')  # take input command as string
            x = eval(cmd)   # execute the code
            if x:   # if vlue is returned
                print(x)    # print it

        except:   # if error occures, return it
            print(format_exc())