#!/usr/bin/env python3

import math
import numpy as np
import os
import socket
import sys
import time
from random import random

from animator import Animator
from client import Client
from effect_base import EffectBase
from sim_client import SimClient
from utils import PixelMap, calc_affine, hsl_to_rgb

TARGET_FPS = 30
SPEED = 0.75

class PlaneWaveEffect(EffectBase):
    def reset(self):
        self._speed = SPEED

        self._progress = -2
        self._current_map = self._map
        self._current_color = (1, 1, 1)


    def animate(self, delta_t):
        # Find our current progress
        self._progress = (self._speed * delta_t) + self._progress
        if self._progress > 2:
            self._progress = -2

            # Pick an orientation at random
            x = random() * 2 * math.pi
            y = random() * 2 * math.pi
            z = random() * 2 * math.pi
            transform_mat = calc_affine(x, y, z)
            self._current_map = self._map.transform(transform_mat)

            # Choose a random hue
            hue = random() * 360.0
            self._current_color = hsl_to_rgb(hue, 1.0, 1.0)

        buffer = bytearray()
        red, green, blue = self._current_color
        for pixel in self._current_map:
            gaussian = self.gaussian(pixel.coords()[2], self._progress)
            intensity_data = self.intensity_data(red, green, blue, gaussian)
            buffer.extend(intensity_data)
        return buffer

    def gaussian(self, value, offset):
        return math.e ** (-(value + offset) ** 2 * 250)

    def intensity_data(self, red, green, blue, intensity):
        return b''.join([
                int(256 * red * intensity).to_bytes(1, 'big'),
                int(256 * green * intensity).to_bytes(1, 'big'),
                int(256 * blue * intensity).to_bytes(1, 'big')
        ])


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'sim':
        pixel_server = SimClient("./tree_sim.sock")
    else:
        pixel_server = Client(False)

    pixel_map = PixelMap.from_csv(os.getenv("PIXEL_MAP_CSV"))
    plane_anim = PlaneWaveEffect(pixel_map)
    plane_anim.fade_in(1)
    animator = Animator(TARGET_FPS)
    animator.set_animator_target(plane_anim)
    animator.set_pixel_target(pixel_server)
    while True:
        animator.run()

if __name__ == "__main__":
    main()

