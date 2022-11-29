#!/usr/bin/env python3

import math
import numpy as np
import os
import socket
import sys
import time
from random import random

from animator import Animator
from pixel_client import PixelClient
from pixel_sim_client import PixelSimClient
from utils import PixelMap, calc_affine, hsl_to_rgb

TARGET_FPS = 30

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
            hue = random() * 360.0
            self._current_color = hsl_to_rgb(hue, 1.0, 1.0)
            print(hue, self._current_color)

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
    #    pixel_server = PixelClient()
    pixel_server = PixelSimClient("./tree_sim.sock")

    pixel_map = PixelMap.from_csv(os.getenv("PIXEL_MAP_CSV"))
    plane_anim = PlaneWaveEffect(pixel_map, 0.2, 0)
    animator = Animator(plane_anim, pixel_server, TARGET_FPS)
    animator.run()

if __name__ == "__main__":
    main()

