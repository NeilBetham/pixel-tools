#!/usr/bin/env python3

import os
import socket


class PixelClient():
    def __init__(self, ip, port):
        self._ip = ip
        self._port = port
        self._connect()

    def __init__(self):
        self._ip = os.environ['TARGET_IP']
        self._port = int(os.environ['TARGET_PORT'])
        self._connect()

    def __del__(self):
        self._socket.close()

    def send_frame(self, frame):
        sent = self._socket.sendall(frame)
        self._socket.recv(4)
        return sent

    def _connect(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._ip, self._port))

