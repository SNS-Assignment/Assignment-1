#!/usr/bin/env python3

class User:
    def __init__(self, id: str, roll: int, password: str):
        self.id = id
        self.roll = roll
        self.password = password


class Client:
    def __init__(self, userid: str, ip: str, port: int, pubkey=None):
        self.userid = id
        self.ip = ip
        self.port = port
        self.pubkey = ('' if pubkey is None else pubkey)


class Group:
    def __init__(self, name, nonce=None):
        self.name = name
        self.members = []
        self.nonce = ('' if nonce is None else nonce)

    def addMember(self, member: str):
        self.members.append(member)


PIECE_SIZE = 4096
LOCALHOST = '127.0.0.1'
SERVER_PORT = 5000
COMMAND_LIST = ['signup', 'login', 'quit', 'join',
                'create', 'list', 'senduser', 'sendgrp']
