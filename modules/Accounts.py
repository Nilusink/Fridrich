from modules.cryption_tools import low
from json import loads, dumps

class manager:
    def __init__(self, accfile):
        self.crypFile = accfile

    def getAccs(self):
        accs = loads(low.decrypt(open(self.crypFile, 'r').read()))
        return accs

    def writeAccs(self, accs:dict):
        cryp = low.encrypt(dumps(accs))
        with open(self.crypFile, 'w') as out:
            out.write(cryp)

    def setPwd(self, username, password):
        acclist = self.getAccs() # getting and decrypting accounts list
        for element in acclist:
            if element['Name'] == username:
                element['pwd'] = password  # if user is selected user, change its password
                continue    # to not further iterate all users

        self.writeAccs(acclist) # write output to file

    def setUserN(self, oldUser, newUser):
        acclist = self.getAccs() # getting and decrypting accounts list
        for i, element in enumerate(acclist):
            if element['Name'] == oldUser:
                element['Name'] = newUser  # if user is selected user, change its password
                continue    # to not further iterate all users and get i value of element

        acclist[i] = element    # make sure the new element is in list and on correct position

        self.writeAccs(acclist) # write output to file

    def newUser(self, username, password, secClearance):
        accs = self.getAccs()
        print(username, password, secClearance)
        accs.append({'Name':username, 'pwd':password, 'sec':secClearance})
        print(accs)
        self.writeAccs(accs)
