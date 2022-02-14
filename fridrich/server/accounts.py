"""
used for managing user Accounts
(Server)

author: Nilusink
"""
from contextlib import suppress
from typing import List
import random
import json
import os


class Manager:
    """
    account manager
    """

    def __init__(self, account_file: str) -> None:
        """
        account_file - file to store encrypted account data in
        """
        self.__encryptionFile = account_file

        self.__accounts = self.__get_file()

    @property
    def names(self) -> List[str]:
        return [user["Name"] for user in self.__accounts]

    def __get_file(self) -> list:
        """
        decrypt the user passwords with threads
        """
        return json.load(open(self.__encryptionFile))

    def __write_accounts(self, accounts: list) -> None:
        """
        write account file
        """
        self.__accounts = accounts
        with open(self.__encryptionFile, 'w') as out:
            json.dump(self.__accounts, out, indent=4)

    def get_accounts(self) -> list:
        """
        get account data
        """
        return self.__accounts

    def set_pwd(self, username: str, new_password: str) -> None:
        """
        set password of given user
        """
        for element in self.__accounts:
            if element['Name'] == username:
                element['pwd'] = new_password  # if user is selected user, change its password
                break  # to not further iterate all users

        self.__write_accounts(self.__accounts)  # write output to file

    def set_username(self, old_user: str, new_user: str) -> None:
        """
        change username
        """
        used_names = self.names
        used_names.remove(old_user)

        element = str()
        i = int()

        # name+'2' because the double-vote agent uses this for their votes
        if new_user not in used_names + [name + '2' for name in used_names]:
            for i, element in enumerate(self.__accounts):
                if element['Name'] == old_user:
                    element['Name'] = new_user  # if user is selected user, change its password
                    continue

            self.__accounts[i] = element  # make sure the new element is in list and on correct position

            self.__write_accounts(self.__accounts)  # write output to file
            return
        raise NameError('Username already exists')

    def set_user_sec(self, username: str, security_clearance: str) -> None:
        """
        set clearance of user
        """
        element = str()
        i = int()

        for i, element in enumerate(self.__accounts):
            if element['Name'] == username:
                element['sec'] = security_clearance  # if user is selected user, change its security clearance
                continue

        self.__accounts[i] = element  # make sure the new element is in list and on correct position
        self.__write_accounts(self.__accounts)

    def new_user(self, username: str, password: str, security_clearance: str) -> None:
        """
        add new user
        """
        # variables
        new_acc: dict
        ids: list
        new_id: int

        if username in self.names:
            raise NameError(f'Username {username} already exists: {self.names}')

        # create new id for user
        ids = [user["id"] for user in self.__accounts]
        new_id = random.randint(10000, 99999)

        if len(ids) >= 90000:
            raise NotImplementedError("Too many accounts registered!")

        while new_id in ids:
            new_id = random.randint(10000, 99999)

        # add account
        new_acc = {
            'Name': username,
            'pwd': password,
            'sec': security_clearance,
            "id": new_id
        }

        self.__accounts.append(new_acc)  # create user

    def remove_user(self, username: str) -> None:
        """
        remove a user
        """
        accounts = self.get_accounts()  # get accounts
        for i in range(len(accounts)):  # iterate accounts
            if accounts[i]['Name'] == username:  # if account name is username
                accounts.pop(i)  # remove user
                break

        self.__write_accounts(accounts)  # update accounts

    def verify(self, username: str, password: str) -> (None | bool, dict):
        """
        return False or user security Clearance
        """
        users = self.get_accounts()  # get accounts
        auth = False
        user = {}
        for element in users:  # iterate users
            if username == element['Name'] and password == element['pwd']:  # if username is account name
                if 'sec' in element:
                    if element['sec'] == '':
                        auth = None
                        continue
                    user = element
                    auth = True
                    break

        return auth, user  # return result


# user configuration
USER_CONFIG: dict = {}
try:
    USER_CONFIG = json.load(open(os.getcwd() + '/config/user_config.json', 'r'))

except FileNotFoundError:
    with suppress(FileNotFoundError):
        USER_CONFIG = json.load(open('/home/apps/Fridrich/config/user_config.json', 'r'))
