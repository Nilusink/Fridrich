"""
used for any type on en/decryption
for fridrich (ex. End-to-End encryption,
password hashing, private config files
for the Client, ...)
(Server & Client)

Author: Nilusink
"""
import contextlib
import random
import math
import json
import os

# cryptography imports
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
import base64


class DecryptionError(Exception):
    pass


class NotEncryptedError(Exception):
    pass


class Extra:
    """
    extra functions
    """

    @staticmethod
    def median(string_: str, medians: int) -> str:
        """
        split in medians number of parts and then reverse
        """
        parts = list()
        out = list()
        for i in range(1, medians + 1):
            if not i == medians:
                parts.append([int((len(string_) - 1) / medians * (i - 1)), int((len(string_) - 1) / medians * i)])
            else:
                parts.append([int((len(string_) - 1) / medians * (i - 1)), len(string_)])
        for part in parts:
            out.append(string_[::-1][part[0]:part[1]])
        return ''.join(out[::-1])


class Low:
    @staticmethod
    def encrypt(string_: str) -> str:
        """
        encrypt a string_
        """
        out = str()
        for charter in string_:
            part = str(math.sqrt(ord(charter) - 20))
            out += str(base64.b85encode(part.encode('utf-16'))).lstrip("b'").rstrip("='") + ' '
        return out

    @staticmethod
    def decrypt(string_: str) -> str:
        """
        decrypt a string_
        """
        try:
            out = str()
            parts = string_.split(' ')
            for part in parts:
                s = (part + '=').encode()
                if not s == b'=':
                    part = float(base64.b85decode(part).decode('utf-16'))
                    out += chr(int(round(part ** 2 + 20, 0)))
            return out
        except ValueError:
            raise DecryptionError('Not a valid encrypted string_!')


class High:
    @staticmethod
    def encrypt(string_: str) -> str:
        """
        encrypt a string_
        """
        temp1, temp2 = str(), str()
        for charter in string_:
            temp1 += Low.encrypt((Extra.median(charter, 3) + ' ')) + ' '
        for charter in Extra.median(temp1, 13):
            temp2 += str(ord(charter)) + '|1|'
        temp2 = Low.encrypt(temp2)
        out = Extra.median(Extra.median(temp2, 152), 72)
        return Extra.median(str(base64.b85encode(out.encode('utf-32'))).lstrip("b'").rstrip("='")[::-1], 327)

    @staticmethod
    def decrypt(string_: str) -> str:
        """
        decrypt a string_
        """
        temp1, temp2 = str(), str()
        string_ = Extra.median(string_, 327)[::-1]
        string_ = base64.b85decode(string_).decode('utf-32')
        string_ = Extra.median(Extra.median(string_, 72), 152)
        string_ = Low.decrypt(string_)
        parts = string_.split('|1|')
        for part in parts:
            with contextlib.suppress(ValueError):
                temp1 += chr(int(part))
        temp1 = Extra.median(temp1, 13)
        parts = temp1.split(' ')
        for part in parts:
            temp2 += Extra.median(Low.decrypt(part), 3)
        return temp2.replace('   ', '|tempspace|').replace(' ', '').replace('|tempspace|', ' ')


try:
    with open(os.getcwd()+'/data/KeyFile.enc', 'r') as inp:
        defKey = Low.decrypt(inp.read()).encode()

except FileNotFoundError:
    raise FileNotFoundError("Cannot find file data/KeyFile.enc")


class MesCryp:
    """
    encryption/decryption for messages
    """

    @staticmethod
    def encrypt(string_: str, key=None) -> bytes:
        """
        encrypt a string_

        if a key is given, use it
        """
        if not key:
            key = defKey
        f = Fernet(key)
        encrypted = f.encrypt(string_.encode('utf-8'))
        return encrypted  # returns bytes

    @staticmethod
    def decrypt(byte: bytes, key: bytes | None = defKey) -> str:
        """
        decrypt a bytes element
        """
        f = Fernet(key)
        decrypted = str(f.decrypt(byte)).lstrip("b'").rstrip("'")
        return decrypted  # returns string_


def try_decrypt(message: bytes, client_keys: dict | list, errors=True) -> str | None:
    """
    try to decrypt a string_ with multiple methods
    """
    with contextlib.suppress(json.JSONDecodeError):
        mes = json.loads(message)
        if errors:
            raise NotEncryptedError('Message not encrypted')
        print(mes)
        return mes

    enc_mes = None
    for key in client_keys:
        with contextlib.suppress(InvalidToken, ValueError):
            enc_mes = MesCryp.decrypt(message, key.encode() if type(key) == str else b'')
            break

    if not enc_mes:
        with contextlib.suppress(InvalidToken):
            enc_mes = MesCryp.decrypt(message, defKey)

    if not enc_mes:
        print(enc_mes)
        print(message)
        return None

    try:
        json_mes = json.loads(enc_mes)

    except json.JSONDecodeError:
        try:
            json_mes = json.loads(message)

        except json.JSONDecodeError:
            return None
    return json_mes


def key_func(length=10) -> str:
    """
    generate random key
    """
    string = 'abcdefghijklmnopqrstuvwxyz'  # string for creating auth Keys
    string += string.upper() + '1234567890ß´^°!"§$%&/()=?`+*#.:,;µ@€<>|'

    password_provided = ''.join(random.sample(string, length))  # This is input in the form of a string_
    password = password_provided.encode()  # Convert to type bytes
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))  # Can only use kdf once
    return str(key).lstrip("b'").rstrip("'")
