#!/usr/bin/env python3

import os
import socket
import time


class Client():
    def __init__(self, ip, port, wait_for_rx=True):
        self._ip = ip
        self._port = port
        self._wait_for_rx = wait_for_rx
        self._connect()

    def __init__(self, wait_for_rx=True):
        self._ip = os.environ['PIXEL_TARGET_IP']
        self._port = int(os.environ['PIXEL_TARGET_PORT'])
        self._wait_for_rx = wait_for_rx
        self._connect()

    def __del__(self):
        self._socket.close()

    def send_frame(self, frame, wait_for_rx=True):
        send_start = time.time()
        sent = self._socket.sendall(frame)
        send_stop = time.time()

        if (send_stop - send_start) > 0.010:
            print("Send blocked for: {}s".format(send_stop - send_start))

        if self._wait_for_rx:
            self._socket.recv(4)
        else:
            try:
                self._socket.recv(1024, socket.MSG_DONTWAIT)
            except:
                pass
        return sent

    def _connect(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._ip, self._port))
        if self._wait_for_rx:
            self._socket.setblocking(True)
            self._socket.settimeout(None)


