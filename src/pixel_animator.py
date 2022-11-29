#!/usr/bin/env python3

import math
import numpy as np
import os
import socket
import sys
import time
from random import random

from pixel_client import PixelClient
from pixel_sim_client import PixelSimClient
from utils import PixelMap, calc_affine, hsl_to_rgb

PIXEL_LOCATION_CSV = "pixel_map.raw.csv"
LOOP_TIME = 1 / 30

# The animator class is responsible for dispatching animations out the different
# effect classes and then send the result to the pixels
class Animator():
    def __init__(self):
        self._last_anim_exec = time.time()
        self._anim_target = None
        self._pixel_target = None

    def animate(self):
        start_time = time.time()
        if self._anim_target:
            pixel_bytes = self._anim_target.animate(start_time - self._last_anim_exec)
            if self._pixel_target:
                self._pixel_target.send_frame(pixel_bytes)
        self._last_anim_exec = start_time

    def set_animator_target(self, target):
        self._anim_target = target

    def set_pixel_target(self, target):
        self._pixel_target = target


class PlaneWaveEffect():
    def __init__(self, pixel_map, speed, color):
        self._map = pixel_map
        self._speed = speed
        self._color = color

        self._progress = 0
        self._current_map = self._map
        self._current_color = (1, 1, 1)


    def animate(self, delta_t):
        # Find our current progress
        self._progress = (self._speed * delta_t) + self._progress
        if self._progress > 1.5:
            self._progress -= 1.5

            # Pick an orientation at random
            x = random() * 2 * math.pi
            y = random() * 2 * math.pi
            z = random() * 2 * math.pi
            transform_mat = calc_affine(x, y, z)
            self._current_map = self._map.transform(transform_mat)

            # Choose a random hue
            hue = random() * 360
            self._current_color = hsl_to_rgb(hue, 1.0, 1.0)

        buffer = bytearray()
        red, green, blue = self._current_color
        for pixel in self._current_map:
            gaussian = self.gaussian(pixel.normalized_coords()[2], self._progress - 1.1)
            intensity_data = self.intensity_data(red, green, blue, gaussian)
            buffer.extend(intensity_data)
        return buffer

    def gaussian(self, value, offset):
        return math.e ** (-(value + offset) ** 2 * 1500)

    def intensity_data(self, red, green, blue, intensity):
        return b''.join([
                int(256 * red * intensity).to_bytes(1, 'big'),
                int(256 * green * intensity).to_bytes(1, 'big'),
                int(256 * blue * intensity).to_bytes(1, 'big')
        ])


def main():
    pixel_server = PixelClient()
#    pixel_server = PixelSimClient("./tree_sim.sock")

    pixel_map = PixelMap.from_csv(sys.argv[1])
    animator = Animator()
    plane_anim = PlaneWaveEffect(pixel_map, 0.2, 0)
    animator.set_pixel_target(pixel_server)
    animator.set_animator_target(plane_anim)

    while True:
        start_time = time.time()
        animator.animate()
        stop_time = time.time()
        delta_time = stop_time - start_time
        sleep_time = LOOP_TIME - delta_time
        print(sleep_time)
        if sleep_time > 0:
            time.sleep(sleep_time)



if __name__ == "__main__":
    main()

