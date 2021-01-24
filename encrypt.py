#!/usr/bin/env python3

import pyDes
import binascii


class TripleDES:

    @staticmethod
    def encrypt(plaintext, secret):
        des = pyDes.triple_des(secret)  # 16 or 24 bytes
        x = des.encrypt(plaintext, padmode=pyDes.PAD_PKCS5)
        x = binascii.b2a_hex(x).decode(encoding='utf-8')
        return x

    @staticmethod
    def decrypt(ciphertext, secret):
        des = pyDes.triple_des(secret)
        x = binascii.a2b_hex(ciphertext)
        x = des.decrypt(x, padmode=pyDes.PAD_PKCS5)
        return str(x, 'utf-8')


class DiffieHelman:

    P = 2**128-159
    G = 5

    @staticmethod
    def power(x, y, p):
        res = 1
        x = x % p
        if (x == 0):
            return 0
        while (y > 0):
            if ((y & 1) == 1):
                res = (res * x) % p
            y = y >> 1
            x = (x * x) % p
        return res

    @staticmethod
    def getPubKey(pvt_key):
        h = hex(DiffieHelman.power(DiffieHelman.G,int(pvt_key, 16), DiffieHelman.P))
        h = h.upper()
        if h.startswith('0X'):
            h = h[2:]
            return h

    @staticmethod
    def getSecret(pub_key,pvt_key):
        h = hex(DiffieHelman.power(int(pub_key, 16),int(pvt_key, 16), DiffieHelman.P))
        h = h.upper()
        if h.startswith('0X'):
            h = h[2:]
        return h[-16:]
