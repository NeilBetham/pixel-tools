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
from utils import PixelMap, calc_affine, calc_affine2, hsl_to_rgb

TARGET_FPS = 30
SPEED = 2

class BeachballEffect(EffectBase):
    def reset(self):
        self._speed = SPEED

        self._progress = 0
        self._current_map = self._map

        self._rotated_map = self._map.transform(calc_affine2(0, math.pi / 2, 0, -0.75, 0, 0))
        self._polar_map = {}

        for pixel in self._rotated_map:
            x, y, z = pixel.coords()
            self._polar_map[pixel.index()] = math.atan2(y, x) + math.pi

    def animate(self, delta_t):
        # Find our current progress
        self._progress = (self._speed * delta_t) + self._progress
        if self._progress > 2 * math.pi:
            self._progress = 0

        buffer = bytearray()
        for pixel in self._current_map:
            current_offset = self._progress * 180 / math.pi
            pixel_radians = (self._polar_map[pixel.index()] + self._progress) * 180 / math.pi
            red, green, blue = hsl_to_rgb(pixel_radians, 1.0, 1.0)
            intensity_data = self.intensity_data(red, green, blue, 1.0)
            buffer.extend(intensity_data)
        return buffer

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
    plane_anim = BeachballEffect(pixel_map)
    animator = Animator(plane_anim, pixel_server, TARGET_FPS)
    animator.run()

if __name__ == "__main__":
    main()

