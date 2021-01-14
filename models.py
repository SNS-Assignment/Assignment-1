#!/usr/bin/env python3

class User:
    def __init__(self, id: str, password: str):
        self.id = id
        self.password = password


class Client:

    def __init__(self, userid: str, ip: str, port: int):
        self.userid = id
        self.ip = ip
        self.port = port


class Group:
    def __init__(self, name):
        self.name = name
        self.members = []

    def addMember(self, member: str):
        self.members.append(member)


PIECE_SIZE = 4096
LOCALHOST = '127.0.0.1'
SERVER_PORT = 5000
COMMAND_LIST = ['signup', 'login', 'quit', 'join',
                'create', 'list', 'senduser', 'sendgrp']
