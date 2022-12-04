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
from utils import PixelMap, calc_affine, calc_affine2, hsl_to_rgb

TARGET_FPS = 30

class PinWheelEffect():
    def __init__(self, pixel_map, speed, color):
        self._map = pixel_map.transform(calc_affine2(0, 0, 0, 0, 0, -0.5))
        self._speed = speed
        self._color = color

        self._progress = 0
        self._current_map = self._map
        self._current_color = (1, 1, 1)


    def animate(self, delta_t):
        # Find our current progress
        self._progress = (self._speed * delta_t) + self._progress
        if self._progress > math.pi:
            self._progress = -math.pi

            # Choose a random hue
            hue = random() * 360.0
            self._current_color = hsl_to_rgb(hue, 1.0, 1.0)

        # Rotate the tree based on progress
        self._current_map = self._map.transform(calc_affine(self._progress, 0.0, 0.0))

        buffer = bytearray()
        red, green, blue = self._current_color
        for pixel in self._current_map:
            gaussian = self.gaussian(pixel.coords()[2], 0)
            gaussian2 = self.gaussian(pixel.coords()[1], 0)
            intensity_data = self.intensity_data(red, green, blue, min(gaussian + gaussian2, 1.0))
            buffer.extend(intensity_data)
        return buffer

    def gaussian(self, value, offset):
        return math.e ** (-(value + offset) ** 2 * 100)

    def intensity_data(self, red, green, blue, intensity):
        return b''.join([
                int(255 * red * intensity).to_bytes(1, 'big'),
                int(255 * green * intensity).to_bytes(1, 'big'),
                int(255 * blue * intensity).to_bytes(1, 'big')
        ])


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'sim':
        pixel_server = PixelSimClient("./tree_sim.sock")
    else:
        pixel_server = PixelClient()

    pixel_map = PixelMap.from_csv(os.getenv("PIXEL_MAP_CSV"))
    plane_anim = PinWheelEffect(pixel_map, 1, 0)
    animator = Animator(plane_anim, pixel_server, TARGET_FPS)
    animator.run()

if __name__ == "__main__":
    main()

