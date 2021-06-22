from json import load, dump

class VOTES:    # class for votes "variable"
    def __init__(self, getFile, *args): # spciefie main file and other files to update
        self.getFile = getFile
        self.FilesToWrite = args
    
    def get(self):  # get variable from main file
        odict = load(open(self.getFile, 'r'))
        return odict
    
    def write(self, newValue:dict): # write variable to all files
        dump(newValue, open(self.getFile, 'w'), indent=4)

        for element in self.FilesToWrite:
            dump(newValue, open(element, 'w'), indent=4)

class DoubleVote:
    globals()
    def __init__(self, filePath):
        global validUsers
        self.filePath = filePath

        try:
            value = load(open(self.filePath, 'r'))

        except FileNotFoundError:
            value = dict()
            for element in validUsers:
                value[element['Name']] = 1
        
        dump(value, open(self.filePath, 'w'))
    
    def read(self):
        return load(open(self.filePath, 'r'))
    
    def write(self, value:dict):
        print('updating Write')
        dump(value, open(self.filePath, 'w'))

    def vote(self, vote, User):
        print('called double vote')
        global Vote

        votes = Vote.get()
        value = self.read()
        if value[User] < 1:
            return False
        
        votes[User+'2'] = vote
        Vote.write(votes)

        print('set votes:', Vote.get())

        value[User] -= 1
        self.write(value)
        return True

    def unVote(self, User):
        global Vote

        votes = Vote.get()
        with suppress(NameError):
            votes.pop(User+'2')
        
        value = self.read()
        if User in value:
            value[User]+=1
        
        self.write(value)

        Vote.write(votes)
    
    def getFrees(self, User):
        value = self.read()
        if User in value:
            return value[User]
        
        self.write(value)
        return False
