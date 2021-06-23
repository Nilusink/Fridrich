from contextlib import suppress
from math import sqrt
import base64

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
            raise ValueError('Not a valid encrypted string!')

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