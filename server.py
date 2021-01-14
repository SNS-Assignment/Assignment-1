#!/usr/bin/env python3

import os
import socket
import mimetypes
from _thread import *

from models import *

listenSocket: socket

userDatabase = {}
groups = {}
connectedIPS = []
connectedClients = {}


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
            user = User(params[1], params[2])
            if params[1] in userDatabase:
                msg = f'User {params[1]} already exists'
            else:
                msg = f'User {params[1]} registered'
                userDatabase[params[1]] = user
            conn.send(str.encode(msg))
        elif msgType == 'login':
            user = User(params[1], params[2])
            client = Client(params[1], str(addr[1]), int(addr[2]))
            if params[1] not in userDatabase:
                msg = f'User {params[1]} is not registered'
            elif params[1] in connectedClients:
                msg = f'User {params[1]} is already logged in'
            elif params[2] != userDatabase[params[1]].password:
                msg = 'Incorrect password'
            else:
                msg = f'User {params[1]} logged in'
                loginId = params[1]
                connectedClients[params[1]] = client
            conn.send(str.encode(msg))
        elif msgType == 'join':
            if params[1] not in groups:
                msg = f'Creating group {params[1]}\nAdding {loginId} to group'
                grp = Group(params[1])
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
            grpList = str(groups.keys())
            msg = str(grpList)
            conn.send(str.encode(msg))
        elif msgType == 'create':
            if params[1] not in groups:
                msg = f'Creating group {params[1]}'
                grp = Group(params[1])
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
                s = socket.socket()
                client = connectedClients[params[1]]
                try:
                    s.connect((client.ip, client.port))
                    s.send(str.encode(f'{loginId} said {params[3]}'))
                    msg = f'Message sent to user {params[1]}'
                    s.close()
                except Exception as e:
                    print('Exception occured:', str(e))
                    msg = f'Failed to send message to user {params[1]}'
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


def main():
    global listenSocket
    listenSocket = socket.socket()
    try:
        listenSocket.bind((LOCALHOST, SERVER_PORT))
    except Exception as e:
        print('Bind Failed. Exception occured:', str(e))
    listenSocket.listen(4)  # max queued clients=4
    print('Listening on http://' + LOCALHOST + ':' + str(SERVER_PORT))
    start_new_thread(startListen, ())
    print('HIT ENTER TO EXIT')
    input()
    # connectServer()


if __name__ == "__main__":
    main()
