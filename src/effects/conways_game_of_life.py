#!/usr/bin/env python3

import math
import numpy as np
import os
import socket
import sys
import time
from random import random

import numpy as np
from animator import Animator
from client import Client
from effect_base import EffectBase
from sim_client import SimClient
from utils import PixelMap, calc_affine, hsl_to_rgb

TARGET_FPS = 30
CELL_SIZE = 0.25
SPEED = 0.75


# 4555 or 5766
class GameOfLife3D():
    def __init__(self, x, y, z):
        self._game_board = np.zeros((x, y, z))
        self._x = x
        self._y = y
        self._z = z


        # Randomly init game board
        for x_index in range(0, x):
            for y_index in range(0, y):
                for z_idnex in range(0, z):
                    self._game_board[x_index][y_index][z_index] = 0 if random() < 0.5 else 1

    def step(self):
        for x_index in range(0, self._x):
            for y_index in range(0, self._y):
                for z_index in range(0, self._z):
                    ln = live_neighbors(x_index, y_index, z_index)
                    if  ln < 4 or ln > 5:
                        # Cell dies
                        pass
                    if ln == 5:
                        # Cell lives
                        pass
                    else:
                        # Do nothing
                        pass

    def live_neighbors(self, x, y, z):
        pass


class ConwaysGameOfLifeEffect(EffectBase):
    def reset(self):
        self._game_map = []

    def animate(self, delta_t):
        pass

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'sim':
        pixel_server = SimClient("./tree_sim.sock")
    else:
        pixel_server = Client(False)

    pixel_map = PixelMap.from_csv(os.getenv("PIXEL_MAP_CSV"))
    cgol_anim = ConwaysGameOfLifeEffect(pixel_map)
    cgol_anim.fade_in(1)
    animator = Animator(TARGET_FPS)
    animator.set_animator_target(cgol_anim)
    animator.set_pixel_target(pixel_server)
    while True:
        animator.run()

if __name__ == "__main__":
    main()

