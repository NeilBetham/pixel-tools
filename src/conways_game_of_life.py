#!/usr/bin/env python3

import numpy as np
import sys
from random import random

from animator import Animator
from effect_base import EffectBase
from sim_client import SimClient
from utils import PixelMap, hsl_to_rgb

TARGET_FPS = 30
LIVE_START_THREASHOLD = 0.5
GRID_SIZE = 30

class ConwaysGameOfLifeEffect(EffectBase):
    def reset(self):
        self._grid = np.ndarray([GRID_SIZE, GRID_SIZE, GRID_SIZE])
        with np.nditer(self._grid, op_flags=['readwrite']) as grid_it:
            for elem in grid_it:
                elem[...] = 1.0 if random() > LIVE_START_THRESHOLD else 0.0

    def animate(self, delta_t):
        return bytearray(500)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'sim':
        pixel_server = PixelSimClient('./tree_sim.sock')
    else:
        pixel_server = Client()

    pixel_map = PixelMap.from_csv(os.getenv('PIXEL_MAP_CSV'))
    effect = ConwaysGameOfLifeEffect(pixel_map)
    animator = Animator(TARGET_FPS)
    animator.set_animation_target(effect)
    animator.set_pixel_target(pixel_server)
    while True:
        animator.run()

if __name__ == '__main__':
    main()
