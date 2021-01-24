#!/usr/bin/env python3

import copy
import mimetypes
import os
import socket
from _thread import *
import uuid

from models import *

listenSocket: socket

userDatabase = {}
groups = {}
connectedIPS = []
connectedClients = {}
publicKeys = {}


def startListen():
    while True:
        c, a = listenSocket.accept()
        print('Client', a[0], ':', a[1], 'connected')
        data = (c.recv(PIECE_SIZE)).decode('utf-8')
        text = data.split(' ')
        print('Listen IP', text[1], ':', text[2])
        if text[0] == 'sync':
            fullAddress = f'{text[1]}:{text[2]}'
            if fullAddress in connectedIPS:
                print(f'{fullAddress} is already connected')
                continue
            else:
                connectedIPS.append(fullAddress)

        start_new_thread(acceptMessage, (c, text))
    listenSocket.close()


def acceptMessage(conn, addr):
    loginId = ''
    while True:
        data = (conn.recv(PIECE_SIZE))
        text = data.decode('utf-8')
        print(f'{addr[1]}:{addr[2]} said {text}')
        params = text.split(' ')
        msgType = params[0]
        if msgType == 'signup':
            user = User(params[1], params[2], params[3])
            if params[1] in userDatabase:
                msg = f'User {params[1]} already exists'
            else:
                msg = f'User {params[1]} registered'
                userDatabase[params[1]] = user
            conn.send(str.encode(msg))
        elif msgType == 'login':
            #user = User(params[1], params[2])
            client = Client(params[1], str(addr[1]), int(addr[2]))
            if params[1] not in userDatabase:
                msg = f'User {params[1]} is not registered'
            elif params[1] in connectedClients:
                msg = f'User {params[1]} is already logged in'
            elif params[2] != userDatabase[params[1]].password:
                msg = 'Incorrect password'
            else:
                msg = f'User {params[1]} successfully logged in {userDatabase[params[1]].roll}'
                for c in connectedClients:
                    msg = f'{msg}\n{c} {connectedClients[c].ip} {connectedClients[c].port}'
                loginId = params[1]
                print(msg)
                connectedClients[params[1]] = client
            conn.send(str.encode(msg))
            # if loginId != '':
            #     data = (conn.recv(PIECE_SIZE))
            #     text = data.decode('utf-8')
            #     print(f'Public key received from {loginId}: {text}')
        elif msgType == 'join':
            if params[1] not in groups:
                msg = f'Creating group {params[1]}\nAdding {loginId} to group'
                grp = Group(params[1], uuid.uuid4().hex)
                grp.addMember(loginId)
                groups[params[1]] = grp
            else:
                msg = f'Adding {loginId} to group'
                grp = groups[params[1]]
                if loginId in grp.members:
                    msg = f'{loginId} already present in group {params[1]}'
                else:
                    grp.addMember(loginId)
                    groups[params[1]] = grp
            conn.send(str.encode(msg))
        elif msgType == 'list':
            msg = ''
            for grp in groups:
                msg = msg + \
                    f'\nName: {grp} Participants: {len(groups[grp].members)}'
            # grpList = str(groups.keys())
            # msg = str(grpList)
            conn.send(str.encode(msg))
        elif msgType == 'create':
            if params[1] not in groups:
                msg = f'Creating group {params[1]}'
                grp = Group(params[1], uuid.uuid4().hex)
                groups[params[1]] = grp
            else:
                msg = f'Group {params[1]} already exists'
            conn.send(str.encode(msg))
        elif msgType == 'senduser':
            if params[1] not in userDatabase:
                msg = f'User {params[1]} is not registered'
            elif params[1] not in connectedClients:
                msg = f'User {params[1]} is offline/not logged in'
            else:
                msg = sendToUser(params, loginId)
            conn.send(str.encode(msg))
        elif msgType == 'sendgrp':
            if params[1] not in groups:
                msg = f'Group {params[1]} does not exist'
                conn.send(str.encode(msg))
            else:
                for u in groups[params[1]].members:
                    t = copy.deepcopy(params)
                    t[1] = u
                    msg = sendToUser(t, loginId)
                    conn.send(str.encode(msg))
        elif msgType == 'quit':
            msg = f'{addr[1]}:{addr[2]} ({loginId}) logged out'
            connectedClients.pop(loginId, 'User not entered')
            connectedIPS.remove(f'{addr[1]}:{addr[2]}')
            print(msg)
            conn.close()
            break
        else:
            msg = 'Unknown command'
            conn.send(str.encode(msg))


def sendToUser(params, loginId):

    s = socket.socket()
    client = connectedClients[params[1]]
    s.connect((client.ip, client.port))
    if params[2] == 'text':
        s.send(str.encode('text'))
        s.recv(PIECE_SIZE)
        try:
            # s.close()
            t = ' '.join(params[3:])
            s.send(str.encode(f'{loginId} sent {t}'))
            msg = f'Message sent to user {params[1]}'
        except Exception as e:
            print('Exception occured:', str(e))
            msg = f'Failed to send message to user {params[1]}'
        return msg
    elif params[2] == 'file':
        filename = params[3].split('/')
        filename = filename[-1]
        s.send(str.encode(f'file {loginId} {filename}'))
        s.recv(PIECE_SIZE)
        try:
            with open(params[3], 'rb') as f:
                packet = f.read(PIECE_SIZE)
                while len(packet) != 0:
                    s.send(packet)
                    packet = f.read(PIECE_SIZE)
            msg = f'Message sent to user {params[1]}'
        except Exception as e:
            print('Exception occured:', str(e))
            msg = f'Failed to send message to user {params[1]}'
        return msg


def main():
    global listenSocket
    listenSocket = socket.socket()
    try:
        listenSocket.bind((LOCALHOST, SERVER_PORT))
    except Exception as e:
        print('Bind Failed. Exception occured:', str(e))
        quit()
    listenSocket.listen(4)  # max queued clients=4
    print('Listening on http://' + LOCALHOST + ':' + str(SERVER_PORT))
    start_new_thread(startListen, ())
    print('HIT ENTER TO EXIT')
    input()
    # connectServer()


if __name__ == "__main__":
    main()
