#!/usr/bin/env python3

import datetime
import os
import socket
import sys
from _thread import *

from models import *
import pyDes
import binascii

listenSocket: socket
serverSocket: socket
IS_LOGGED_IN = False
LOGIN_ID = ''
isActive = True
params = list()


def startListen():
    while isActive:
        c, a = listenSocket.accept()
        #print('Client', a[0], ':', a[1], 'connected')
        start_new_thread(acceptMessage, (c, a))
    listenSocket.close()


def connectServer():
    global serverSocket
    serverSocket = socket.socket()
    try:
        serverSocket.connect((LOCALHOST, SERVER_PORT))
    except Exception as e:
        print('Exception occured:', str(e))
        quit()
    print(f'Connected to server on {LOCALHOST}:{SERVER_PORT}')
    serverSocket.send(str.encode(f'sync {LOCALHOST} {sys.argv[1]}'))
    enterCommand()


def encrypt(plaintext):
    des = pyDes.triple_des('123456789123456789123456')
    x = des.encrypt(plaintext, padmode=pyDes.PAD_PKCS5)
    x = binascii.b2a_hex(x).decode(encoding='utf-8')
    return x


def decrypt(ciphertext):
    des = pyDes.triple_des('123456789123456789123456')
    x = binascii.a2b_hex(ciphertext)
    x = des.decrypt(x, padmode=pyDes.PAD_PKCS5)
    return str(x, 'utf-8')


def enterCommand():
    while True:
        cmd = input()
        cmd = cmd.lower()
        cmdList = cmd.split(' ')
        sendCommand = ''
        if cmdList[0] == 'quit':
            global isActive
            isActive = False
            # listenSocket.close()
            serverSocket.send(str.encode(cmd))
            serverSocket.close()
            break
        elif cmdList[0] == 'signup':
            if len(cmdList) < 3:
                print('Too few parameters')
                continue
        elif cmdList[0] == 'login':
            if len(cmdList) < 3:
                print('Too few parameters')
                continue
        elif cmdList[0] == 'join':
            if len(cmdList) < 2:
                print('Too few parameters')
                continue
        elif cmdList[0] == 'create':
            if len(cmdList) < 2:
                print('Too few parameters')
                continue
        # senduser <user_name> <text/file> <text body/file path>
        elif cmdList[0] == 'senduser':
            if len(cmdList) < 4:
                print('Too few parameters')
                continue
            if cmdList[2] != 'text' and cmdList[2] != 'file':
                print('Incorrect format: '+cmdList[2])
                continue
        elif cmdList[0] == 'sendgrp':
            if len(cmdList) < 4:
                print('Too few parameters')
                continue
            if cmdList[2] != 'text' and cmdList[2] != 'file':
                print('Incorrect format: '+cmdList[2])
                continue
        elif cmdList[0] not in COMMAND_LIST:
            print('Unknown command')
            continue
        print(cmd)
        print(type(cmd))
        if cmdList[0] == 'senduser' or cmdList[0] == 'sendgrp':
            msg = ''
            for i in range(3, len(cmdList)):
                msg += cmdList[i]+' '
            msg = encrypt(msg)
            cmd = cmdList[0] + ' ' + cmdList[1] + ' ' + cmdList[2] + ' ' + msg
        serverSocket.send(str.encode(cmd))
        data = (serverSocket.recv(PIECE_SIZE))
        text = data.decode('utf-8')
        print(f'Server response: {text}')


def acceptMessage(conn, addr):
    data = conn.recv(PIECE_SIZE)
    text = data.decode('utf-8')
    conn.send(str.encode('OK'))  # sync mechanism
    if text == 'text':
        data = conn.recv(PIECE_SIZE)
        data = data.decode('utf-8').split(' ')
        print(data[0]+' '+data[1]+' ',end=' ')
        print(decrypt(data[2]))
    else:
        text = text.split(' ')
        fName = text[2]
        f = open(f'{datetime.datetime.now().time()}-{fName}', 'wb')
        while True:
            data = conn.recv(PIECE_SIZE)
            while len(data) != 0:
                f.write(data)
                if len(data) < PIECE_SIZE:
                    break
                data = conn.recv(PIECE_SIZE)
            f.close()
            break
        print(f'{text[1]} sent file {fName}')


def main():
    if len(sys.argv) < 2:
        print('Insuficient parameters')
        return
    global listenSocket
    global serverSocket
    global IS_LOGGED_IN
    global LOGIN_ID
    listenSocket = socket.socket()
    try:
        listenSocket.bind((LOCALHOST, int(sys.argv[1])))
    except Exception as e:
        print('Bind Failed. Exception occured:', str(e))
    listenSocket.listen(4)  # max queued clients=4
    print('Listening on http://' + LOCALHOST + ':' + sys.argv[1])
    start_new_thread(startListen, ())
    connectServer()


if __name__ == "__main__":
    main()
