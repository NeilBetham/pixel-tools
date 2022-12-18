#!/usr/bin/env python3

import os
import socket

class SimClient():
    def __init__(self, socket_path):
        self._socket_path = socket_path
        self._connect()

    def __del__(self):
        self._socket.close()

    def _connect(self):
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(self._socket_path)

    def send_frame(self, frame):
        sent = self._socket.sendall(frame)
        return sent
