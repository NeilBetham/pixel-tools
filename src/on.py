#!/usr/bin/env python3

import time

from client import  Client

PIXEL_COUNT = 1000
BYTE_COUNT = PIXEL_COUNT * 3
MESSAGE_OFF = bytes.fromhex("00") * BYTE_COUNT
MESSAGE_ON = bytes.fromhex("FF") * BYTE_COUNT


def main():
    client = Client()
    sent = client.send_frame(MESSAGE_ON)

if __name__ == "__main__":
    main()
