#!/usr/bin/env python3

import datetime
import os
import socket
import sys
import hashlib
import uuid
from _thread import *

from models import *
from encrypt import TripleDES, DiffieHelman

listenSocket: socket
serverSocket: socket
IS_LOGGED_IN = False
LOGIN_ID = ''
isActive = True
PRIVATE_KEY = ''
PUBLIC_KEY = ''
SECRETS = {}
GROUP_NONCE = {}


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


def enterCommand():
    global LOGIN_ID
    global isActive
    global PRIVATE_KEY
    global PUBLIC_KEY
    while True:
        cmd = input()
        cmd = cmd.lower()
        cmdList = cmd.split(' ')
        sendCommand = ''
        if cmdList[0] == 'quit':
            isActive = False
            LOGIN_ID = ''
            # listenSocket.close()
            serverSocket.send(str.encode(cmd))
            serverSocket.close()
            break
        elif cmdList[0] == 'signup':
            if len(cmdList) < 4:
                print('Too few parameters')
                continue
        elif cmdList[0] == 'login':
            if len(cmdList) < 3:
                print('Too few parameters')
                continue
            if LOGIN_ID != '':
                print('Already logged in')
                continue
            sendCommand = 'login'
        elif cmdList[0] == 'join':
            if len(cmdList) < 2:
                print('Too few parameters')
                continue
            sendCommand = 'join'
        elif cmdList[0] == 'create':
            if len(cmdList) < 2:
                print('Too few parameters')
                continue
            sendCommand = 'create'
        elif cmdList[0] == 'senduser':
            if len(cmdList) < 4:
                print('Too few parameters')
                continue
            if cmdList[2] != 'text' and cmdList[2] != 'file':
                print('Incorrect format: '+cmdList[2])
                continue
            if cmdList[2] == 'file' and not os.path.exists(cmdList[3]):
                print('Incorrect path/file not found:', cmdList[3])
                continue
        elif cmdList[0] == 'sendgrp':
            if len(cmdList) < 4:
                print('Too few parameters')
                continue
            if cmdList[2] != 'text' and cmdList[2] != 'file':
                print('Incorrect format: '+cmdList[2])
                continue
            if cmdList[1] not in GROUP_NONCE:
                print('Not a member of group/Invalid group')
                continue
            if cmdList[2] == 'file' and not os.path.exists(cmdList[3]):
                print('Incorrect path/file not found:', cmdList[3])
                continue
        elif cmdList[0] not in COMMAND_LIST:
            print('Unknown command')
            continue
        # print(cmd)
        # print(type(cmd))
        if (cmdList[0] == 'senduser' or cmdList[0] == 'sendgrp'):
            if cmdList[2] == 'text':
                msg = ''
                for i in range(3, len(cmdList)):
                    msg += cmdList[i]+' '
                msg = TripleDES.encrypt(
                    msg, SECRETS[cmdList[1]] if cmdList[0] == 'senduser' else GROUP_NONCE[cmdList[1]])
                cmd = cmdList[0] + ' ' + cmdList[1] + \
                    ' ' + cmdList[2] + ' ' + msg
            elif cmdList[2] == 'file':
                cmdList[3] = TripleDES.encrypt(
                    cmdList[3], SECRETS[cmdList[1]] if cmdList[0] == 'senduser' else GROUP_NONCE[cmdList[1]])
                cmd = ' '.join(cmdList)
        serverSocket.send(str.encode(cmd))
        data = (serverSocket.recv(PIECE_SIZE))
        text = data.decode('utf-8')
        if sendCommand == 'login' and 'successfully' in text.split('\n')[0]:
            # try:
            svResponse = text.split('\n')[0]
            svResponse = svResponse.split(' ')
            roll = svResponse[-1]
            LOGIN_ID = svResponse[1]
            PRIVATE_KEY = (hashlib.sha256(
                (uuid.uuid4().hex+roll).encode())).hexdigest()[-16:]
            PUBLIC_KEY = DiffieHelman.getPubKey(PRIVATE_KEY)
            # print(PUBLIC_KEY)
            if len(text.split('\n')) > 1:
                syncPublicKey(text.split('\n')[1:])
            # except Exception as e:
            #     print('Exception occured', e)
            #     break
        if (sendCommand == 'create' or sendCommand == 'join') and 'Creating' in text.split('\n')[0]:
            svResponse = (text.split('\n')[2]).strip()
            GROUP_NONCE[svResponse] = uuid.uuid4().hex[-16:]
        if sendCommand == 'join' and 'Adding' in text.split('\n')[0]:
            syncGroupNonce(text.split('\n')[1])
        #text = text.split('\n')[0]
        print(f'Server response: {text}')


def syncPublicKey(ll: list):
    for l in ll:
        x = l.split(' ')
        user = x[0]
        ip = x[1]
        port = x[2]
        userSocket = socket.socket()
        # try:
        userSocket.connect((ip, int(port)))
        userSocket.send(str.encode(f'pubsync {LOGIN_ID} {PUBLIC_KEY}'))
        data = (userSocket.recv(PIECE_SIZE))
        text = data.decode('utf-8')
        text = text.split(' ')
        # print(text)
        SECRETS[text[0]] = DiffieHelman.getSecret(text[1], PRIVATE_KEY)
        userSocket.close()
        # except Exception as e:
        #     print('Exception occured:', str(e))

    # print(SECRETS)


def syncGroupNonce(ll: str):
    x = ll.split(' ')
    grp = x[0]
    ip = x[1]
    port = int(x[2])
    userSocket = socket.socket()
    # try:
    userSocket.connect((ip, port))
    userSocket.send(str.encode(f'grpsync {grp}'))
    data = (userSocket.recv(PIECE_SIZE))
    text = data.decode('utf-8')
    # print(text)
    GROUP_NONCE[grp] = text
    userSocket.close()


def unique_filename(output_filename, file_extension):
    n = ''
    while os.path.exists(f'{output_filename}{n}{file_extension}'):
        if isinstance(n, str):
            n = -1
        n += 1
    return f'{output_filename}{n}{file_extension}'


def acceptMessage(conn, addr):
    data = conn.recv(PIECE_SIZE)
    text = data.decode('utf-8')
    params = text.split(' ')
    if params[0].startswith('file') or params[0].startswith('text'):
        conn.send(str.encode('OK'))  # sync mechanism
    if params[0].startswith('text'):
        data = conn.recv(PIECE_SIZE)
        data = data.decode('utf-8').split(' ')
        key = (GROUP_NONCE[data[4]] if params[0]
               [-1] == 'g' else SECRETS[data[0]])
        data[-1] = TripleDES.decrypt(data[6 if params[0]
                                          [-1] == 'g' else 3], key)
        print(' '.join(data))
    elif params[0].startswith('file'):
        ip = params[2]
        port = int(params[3])
        data = conn.recv(PIECE_SIZE)
        data = data.decode('utf-8').split(' ')
        key = (GROUP_NONCE[data[4]] if params[0]
               [-1] == 'g' else SECRETS[data[0]])
        data[-1] = TripleDES.decrypt(data[6 if params[0]
                                          [-1] == 'g' else 3], key)
        fName = (data[-1].split('/'))[-1]
        print(' '.join(data))
        # try:
        filename, file_ext = os.path.split(fName)
        fName = unique_filename(str(filename), str(file_ext))

        f = open(fName, 'wb')
        fds = socket.socket()
        fds.connect((ip, port))
        if params[0][-1] == 'g':
            fds.send(str.encode(f'dlfile g {data[4]} {data[-1]}'))
        else:
            fds.send(str.encode(f'dlfile u {LOGIN_ID} {data[-1]}'))
        while True:
            data = fds.recv(PIECE_SIZE+8)
            data = TripleDES.decrypt(data, key, isFile=True)
            while len(data) != 0:
                f.write(data)
                if len(data) < PIECE_SIZE:
                    break
                data = fds.recv(PIECE_SIZE+8)
                data = TripleDES.decrypt(data, key, isFile=True)
            f.close()
            break
        print(f'Downloaded file {fName}')
        fds.close()
        # except Exception as e:
        #     print('Exception occured:', str(e))
    elif params[0] == 'pubsync':
        SECRETS[params[1]] = DiffieHelman.getSecret(params[2], PRIVATE_KEY)
        #print(f'{LOGIN_ID} {PUBLIC_KEY}')
        # print(SECRETS)
        conn.send(str.encode(f'{LOGIN_ID} {PUBLIC_KEY}'))
    elif params[0] == 'grpsync':
        conn.send(str.encode(f'{GROUP_NONCE[params[1]]}'))
        # print(GROUP_NONCE)
    elif params[0] == 'dlfile':
        dckey = ''
        print('Uploading file', params[3])
        if params[1] == 'u':
            dckey = SECRETS[params[2]]
        else:
            dckey = GROUP_NONCE[params[2]]
        with open(params[3], 'rb') as f:
            packet = f.read(PIECE_SIZE)
            while len(packet) != 0:
                packet = TripleDES.encrypt(packet, dckey, isFile=True)
                conn.send(packet)
                packet = f.read(PIECE_SIZE)


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
        return
    listenSocket.listen(4)  # max queued clients=4
    print('Listening on http://' + LOCALHOST + ':' + sys.argv[1])
    start_new_thread(startListen, ())
    connectServer()


if __name__ == "__main__":
    main()
