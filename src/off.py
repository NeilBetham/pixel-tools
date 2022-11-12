#!/usr/bin/env python3

import time

from pixel_client import  PixelClient

PIXEL_COUNT = 500
BYTE_COUNT = PIXEL_COUNT * 3
MESSAGE_OFF = bytes.fromhex("00") * BYTE_COUNT
MESSAGE_ON = bytes.fromhex("FF") * BYTE_COUNT


def main():
    client = PixelClient()
    sent = client.send_frame(MESSAGE_OFF)

if __name__ == "__main__":
    main()
