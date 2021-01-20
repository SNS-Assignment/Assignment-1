#!/usr/bin/env python3

import mimetypes
import os
import socket
import sys
from _thread import *

from models import *

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
        serverSocket.send(str.encode(cmd))
        data = (serverSocket.recv(PIECE_SIZE))
        text = data.decode('utf-8')
        print(f'Server response: {text}')


def acceptMessage(conn, addr):
    # global rep
    # print(rep)
    # if rep == False:
    #     data = conn.recv(PIECE_SIZE)
    #     conn.close()
    #     data = data.decode()
    #     print(data)
    #     data = eval(data)
    #     global params
    #     params = data.copy()
    #    # params = eval(params)
    #     print(type(params))
    #     rep = True
    # print(params) 
    data = conn.recv(80).decode()
    print(data)
    data = data.split('del1')
    params = eval(data[0])   
    print(params[2])
    if params[2] == 'text':
        print(sys.getsizeof(params))
        #text = params[3]
        #data = conn.recv(PIECE_SIZE)
        text = data[1]
        data = conn.recv(PIECE_SIZE)
        text += data.decode()
        while data > bytes(1):
            data = conn.recv(PIECE_SIZE)
            text += data.decode()
        print(text)
    elif params[2] == 'file':
        filename = params[3].split('/')
        filename = filename[-1]
        text = data[1]
        print(text)
        f = open(filename,'wb+')
        data = conn.recv(PIECE_SIZE)
        f.write(data)
        while data > bytes(1):
            data = conn.recv(PIECE_SIZE)
            f.write(data)
        f.close()
        #conn.close()    

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
