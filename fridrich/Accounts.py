from fridrich import *
import json


class Manager:
    """
    account manager
    """
    def __init__(self, account_file: str) -> None:
        """
        account_file - file to store encrypted account data in
        """
        self.encryptionFile = account_file
        self.ClientKeys = dict()

    def get_accounts(self) -> list:
        """
        get account data
        """
        accounts = json.loads(cryption_tools.Low.decrypt(open(self.encryptionFile, 'r').read()))
        return accounts

    def write_accounts(self, accounts: list) -> None:
        """
        write account file
        """
        crypt = cryption_tools.Low.encrypt(json.dumps(accounts))
        with open(self.encryptionFile, 'w') as out:
            out.write(crypt)

    def set_pwd(self, username: str, password: str) -> None:
        """
        set password of given user
        """
        account_list = self.get_accounts()  # getting and decrypting accounts list
        for element in account_list:
            if element['Name'] == username:
                element['pwd'] = password  # if user is selected user, change its password
                continue    # to not further iterate all users

        self.write_accounts(account_list)    # write output to file

    def set_username(self, old_user: str, new_user: str) -> None:
        """
        change username
        """
        account_list = self.get_accounts()    # getting and decrypting accounts list
        UsedNames = useful.List.get_inner_dict_values(account_list, 'Name')  # so it doesnt matter if you don't change the username
        UsedNames.remove(old_user)

        element = str()
        i = int()

        if new_user not in UsedNames+[name+'2' for name in UsedNames]:  # name+'2' because the double-vote agent uses this for their votes
            for i, element in enumerate(account_list):
                if element['Name'] == old_user:
                    element['Name'] = new_user  # if user is selected user, change its password
                    continue    # to not further iterate all users and get i value of element

            account_list[i] = element    # make sure the new element is in list and on correct position

            self.write_accounts(account_list)  # write output to file
            return
        raise NameError('Username already exists')

    def set_user_sec(self, username: str, security_clearance: str) -> None:
        """
        set clearance of user
        """
        element = str()
        i = int()

        account_list = self.get_accounts()  # getting and decrypting accounts list
        for i, element in enumerate(account_list):
            if element['Name'] == username:
                element['sec'] = security_clearance  # if user is selected user, change its security clearance
                continue    # to not further iterate all users and get i value of element

        account_list[i] = element    # make sure the new element is in list and on correct position

        self.write_accounts(account_list)  # write output to file

    def new_user(self, username: str, password: str, security_clearance: str) -> None:
        """
        add new user
        """
        accounts = self.get_accounts()
        UsedNames = useful.List.get_inner_dict_values(accounts, 'Name')

        if username in UsedNames:
            raise NameError('Username already exists')

        accounts.append({'Name': username, 'pwd': password, 'sec': security_clearance})  # create user
        self.write_accounts(accounts)    # write user
    
    def remove_user(self, username: str) -> None:
        """
        remove a user
        """
        accounts = self.get_accounts()   # get accounts
        for i in range(len(accounts)):  # iterate accounts
            if accounts[i]['Name'] == username:  # if account name is username
                accounts.pop(i)  # remove user
                break
        
        self.write_accounts(accounts)    # update accounts

    def verify(self, username: str, password: str) -> None | str:
        """
        return False or user security Clearance
        """
        users = self.get_accounts()  # get accounts
        Auth = False
        for element in users:   # iterate users
            if username == element['Name'] and password == element['pwd']:  # if username is account name
                if 'sec' in element:
                    Auth = element['sec']   # set element 'sec' of user
                    if Auth == '':
                        Auth = None
                else:
                    Auth = None

        return Auth  # return result
