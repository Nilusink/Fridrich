from fridrich.cryption_tools import low
from fridrich.useful import List
from json import loads, dumps

class manager:
    "account manager"
    def __init__(self, accfile:str) -> None:
        "accfile - file to store encrypted account data in"
        self.crypFile = accfile

    def getAccs(self) -> dict:
        "get account data"
        accs = loads(low.decrypt(open(self.crypFile, 'r').read()))
        return accs

    def writeAccs(self, accs:dict) -> None:
        "write account file"
        cryp = low.encrypt(dumps(accs))
        with open(self.crypFile, 'w') as out:
            out.write(cryp)

    def setPwd(self, username:str, password:str) -> None:
        "set password of given user"
        acclist = self.getAccs() # getting and decrypting accounts list
        for element in acclist:
            if element['Name'] == username:
                element['pwd'] = password  # if user is selected user, change its password
                continue    # to not further iterate all users

        self.writeAccs(acclist) # write output to file

    def setUserN(self, oldUser:str, newUser:str) -> None:
        "change username"
        acclist = self.getAccs() # getting and decrypting accounts list
        UsedNames = List.getInnerDictValues(acclist, 'Name')  # so it doesnt matter if you don't change the username
        UsedNames.remove(oldUser)

        if not newUser in UsedNames:
            for i, element in enumerate(acclist):
                if element['Name'] == oldUser:
                    element['Name'] = newUser  # if user is selected user, change its password
                    continue    # to not further iterate all users and get i value of element

            acclist[i] = element    # make sure the new element is in list and on correct position

            self.writeAccs(acclist) # write output to file
            return
        raise NameError('Username already exists')

    def setUserSec(self, username:str, SecurityClearance:str) -> None:
        "set clearance of user"
        acclist = self.getAccs() # getting and decrypting accounts list
        for i, element in enumerate(acclist):
            if element['Name'] == username:
                element['sec'] = SecurityClearance  # if user is selected user, change its security clearance
                continue    # to not further iterate all users and get i value of element

        acclist[i] = element    # make sure the new element is in list and on correct position

        self.writeAccs(acclist) # write output to file

    def newUser(self, username:str, password:str, secClearance:str) -> None:
        "add new user"
        accs = list(self.getAccs())   # get accounts
        UsedNames = List.getInnerDictValues(accs, 'Name')

        if username in UsedNames:
            raise NameError('Username already exists')
        accs.append({'Name':username, 'pwd':password, 'sec':secClearance})  # create user
        self.writeAccs(accs)    # write user
    
    def rmUser(self, username:str) -> None:
        "remove user"
        accs = self.getAccs()   # get accounts
        for i in range(len(accs)):  # iterate accounts
            if accs[i]['Name'] == username: #   if account name is username
                accs.pop(i) # remove user
                break
        
        self.writeAccs(accs)    # update accounts

    def verify(self, username:str, password:str):
        "return False or user security Clearance"
        users = self.getAccs()  # get accounts
        Auth = False
        for element in users:   # iterate users
            if username == element['Name'] and password == element['pwd']:  # if username is account name
                if 'sec' in element:
                    Auth = element['sec'], element['Name']   # set element 'sec' of user
                    if Auth == '':
                        Auth = None
                else:
                    Auth = None

        return Auth # return result