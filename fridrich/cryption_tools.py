from json.decoder import JSONDecodeError
from contextlib import suppress
from random import sample
from json import loads
from math import sqrt
import base64

# cryptography
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from os import urandom
import base64

import fridrich.uniReplace as ur

class DecryptionError(Exception):
    pass

class NotEncryptedError(Exception):
    pass

class extra:
    def median(string:str, medians:int):
        parts = list()
        out = list()
        for i in range(1, medians+1):
            if not i==medians:
                parts.append([int((len(string)-1)/medians*(i-1)), int((len(string)-1)/medians*i)])
            else:
                parts.append([int((len(string)-1)/medians*(i-1)), len(string)])
        for part in parts:
            out.append(string[::-1][part[0]:part[1]])
        return ''.join(out[::-1])

class low:
    def encrypt(string:str) -> str:
        out = str()
        for charter in string:
            part = str(sqrt(ord(charter)-20))
            out+=str(base64.b85encode(part.encode('utf-16'))).lstrip("b'").rstrip("='")+' '
        return out

    def decrypt(string:str) -> str:
        try:
            out = str()
            parts = string.split(' ')
            for part in parts:
                s = (part+'=').encode()
                if not s == b'=':
                    part = float(base64.b85decode(part).decode('utf-16'))
                    out += chr(int(round(part**2+20, 0)))
            return out
        except ValueError:
            raise DecryptionError('Not a valid encrypted string!')

class high:
    def encrypt(string:str) -> str:
        temp1, temp2 = str(), str()
        for charter in string:
            temp1 += low.encrypt((extra.median(charter, 3)+' '))+' '
        for charter in extra.median(temp1, 13):
            temp2 += str(ord(charter))+'|1|'
        temp2 = low.encrypt(temp2)
        out = extra.median(extra.median(temp2, 152), 72)
        return extra.median(str(base64.b85encode(out.encode('utf-32'))).lstrip("b'").rstrip("='")[::-1], 327)
    
    def decrypt(string:str) -> str:
        temp1, temp2 = str(), str()
        string = extra.median(string, 327)[::-1]
        string = base64.b85decode(string).decode('utf-32')
        string = extra.median(extra.median(string, 72), 152)
        string = low.decrypt(string)
        parts  = string.split('|1|')
        for part in parts:
            with suppress(ValueError):
                temp1 += chr(int(part))
        temp1 = extra.median(temp1, 13)
        parts = temp1.split(' ')
        for part in parts:
            temp2 += extra.median(low.decrypt(part), 3)
        return temp2.replace('   ', '|tempspace|').replace(' ', '').replace('|tempspace|', ' ')

try:
    with open('/home/pi/Server/data/KeyFile.enc', 'r') as inp:
        defKey = low.decrypt(inp.read()).lstrip("b'").rstrip("'").encode()

except FileNotFoundError:
    with open('data/KeyFile.enc', 'r') as inp:
        defKey = low.decrypt(inp.read())

#defKey = b'fBAXqbIYs0Mvslqzc2eVcpi3mFfXOJdOTsQLNAjU_RQ='

#/home/pi/Server/
class MesCryp:
    def encrypt(string:str, key=None):
        if not key:
            key = defKey
        f = Fernet(key)
        encrypted = f.encrypt(string.encode('utf-8'))
        return encrypted    # returns bytes
    
    def decrypt(byte:bytes, key:bytes):
        f = Fernet(key)
        decrypted = str(f.decrypt(byte)).lstrip("b'").rstrip("'")
        return decrypted    # returns string

def tryDecrypt(message:bytes, ClientKeys, errors=True, repUni=False):
    with suppress(JSONDecodeError):
        mes = loads(ur.decode(message) if repUni else message)
        if errors==True:
            raise NotEncryptedError('Message not encrypted')
        print(mes)
        return mes

    encMes = None
    for key in ClientKeys:
        with suppress((InvalidToken, ValueError)):
            encMes = MesCryp.decrypt(message, key.encode() if type(key)==str else b'')
            break
    
    if not encMes:
        with suppress(InvalidToken):
            encMes = MesCryp.decrypt(message, defKey)
    
    if not encMes:
        print(encMes)
        print(message)
        return None

    try:
        jsonMes = loads(ur.decode(encMes) if repUni else encMes)

    except JSONDecodeError:
        try:
            jsonMes = loads(ur.decode(message) if repUni else message)

        except JSONDecodeError:
            return None
    return jsonMes

def KeyFunc(ClientKeys, length=10): # generate random key
    String = 'abcdefghijklmnopqrstuvwxyz'                               # string for creating auth Keys
    String += String.upper()+'1234567890ß´^°!"§$%&/()=?`+*#.:,;µ@€<>|'

    s = ''.join(sample(String, length)) # try #1
    while s in ClientKeys: 
        s = ''.join(sample(String), length) # if try #1 is already in ClientKeys, try again

    password_provided = s  # This is input in the form of a string
    password = password_provided.encode()  # Convert to type bytes
    salt = urandom(16)  
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))  # Can only use kdf once
    return str(key).lstrip("b'").rstrip("'")

if __name__=='__main__':
    from time import time
    try:
        while True:
            st = input('\n\nSentence? ')
            start = time()
            c = extra.median(low.encrypt(extra.median(st, 12)), 6)
            e = extra.median(low.decrypt(extra.median(c, 6)), 12)
            end = time()
            print('Low encryption:')
            print(c)
            print(e)
            print('\nencrypting and decrypting took:', round(end-start, 2))
            start = time()
            c = MesCryp.encrypt(string=st)
            e = MesCryp.decrypt(c, defKey.encode())
            end = time()
            print('Low encryption:')
            print(c)
            print(e)
            print('\nencrypting and decrypting took:', round(end-start, 2))
            input('Press enter to start high level encryption')
            print('\nHigh encryption:')
            start1 = time()
            c1 = high.encrypt(st)
            end1 = time()
            e1 = high.decrypt(c1)
            end2 = time()
            print(c1)
            print(e1)
            print('\nencrypting took:', round(end1-start1, 2))
            print('decrypting took:', round(end2-end1, 2))
            input('\npress enter to continue\n\n')

    except KeyboardInterrupt:
        print('Closing Client...')
        exit()