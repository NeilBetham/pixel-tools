#!/usr/bin/env python3

import cv2
import os
import pathlib
import socket
import time

from pixel_client import PixelClient

EXPECTED_CAMERA_INDEX = 0
PIXEL_COUNT = 500
MESSAGE_OFF = bytes.fromhex("00" * 3 * PIXEL_COUNT)
MESSAGE_ON = bytes.fromhex("FF" * 3 * PIXEL_COUNT)

class CameraControl():
    def __init__(self):
        self._available_devices = []

        for index in range(10):
            cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                self._available_devices.append(index)
            cap.release()

    def available_devices(self):
        return self._available_devices[::]

    def select_device(self, index):
        self._camera = cv2.VideoCapture(index)
        return self._camera.isOpened()

    def take_image(self, output_location):
        ret, frame = self._camera.read()
        cv2.imwrite(output_location, frame)


class PixelMapper():
    def __init__(self, pixel_count):
        self._pixel_count = pixel_count
        self._ps = PixelClient()
        self._cc = CameraControl()
        self._cc.select_device(EXPECTED_CAMERA_INDEX)
        self._ps.send_frame(self.generate_frame('000000', 0))

    def generate_frame(self, color_bytes, index):
        prefix =  '000000' * index
        postfix = '000000' * (self._pixel_count - index - 1)
        frame_bytes = bytes.fromhex(prefix + color_bytes + postfix)
        return frame_bytes

    def generate_file_name(self, quadrant, pixel_index):
        quad_path = os.getcwd() + '/pixel_maps/{}'.format(quadrant)
        img_path = '{}/{}.png'.format(quad_path, pixel_index)
        pathlib.Path(quad_path).mkdir(parents=True, exist_ok=True)
        return img_path

    def map(self):
        self._cc.select_device(EXPECTED_CAMERA_INDEX)

        for quadrant in range(4):
            print("Imaging Quadrant {}".format(quadrant))
            self._ps.send_frame(bytes('FFFFFF', 'utf-8')*PIXEL_COUNT)
            input("Press enter when ready...")
            self._ps.send_frame(bytes('000000', 'utf-8')*PIXEL_COUNT)
            self._cc.take_image(self.generate_file_name(quadrant, "baseline"))
            for index in range(PIXEL_COUNT):
                self._ps.send_frame(self.generate_frame('FFFFFF', index))
                self._cc.take_image(self.generate_file_name(quadrant, index))
            self._ps.send_frame(MESSAGE_OFF)



def main():
    pm = PixelMapper(PIXEL_COUNT)
    pm.map()


if __name__ == "__main__":
    main()
