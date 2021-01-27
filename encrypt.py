#!/usr/bin/env python3

import binascii

from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad, unpad


class TripleDES:

    @staticmethod
    def encrypt(plaintext, secret, isFile=False):
        if isinstance(plaintext, str):
            plaintext = str.encode(plaintext)
        des = DES3.new(secret, DES3.MODE_ECB)
        x = des.encrypt(pad(plaintext, 8))
        if not isFile:
            x = binascii.b2a_hex(x).decode(encoding='utf-8')
        return x

    @staticmethod
    def decrypt(ciphertext, secret, isFile=False):
        des = DES3.new(secret, DES3.MODE_ECB)
        if not isFile:
            ciphertext = binascii.a2b_hex(ciphertext)
        x = unpad(des.decrypt(ciphertext), 8)
        return (x if isFile else str(x, 'utf-8'))


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
        h = hex(DiffieHelman.power(DiffieHelman.G,
                                   int(pvt_key, 16), DiffieHelman.P))
        h = h.upper()
        if h.startswith('0X'):
            h = h[2:]
            return h

    @staticmethod
    def getSecret(pub_key, pvt_key):
        h = hex(DiffieHelman.power(int(pub_key, 16),
                                   int(pvt_key, 16), DiffieHelman.P))
        h = h.upper()
        if h.startswith('0X'):
            h = h[2:]
        return h[-16:]
