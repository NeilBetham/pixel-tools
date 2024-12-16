#!/usr/bin/env python3

import math
import numpy as np
import os
import socket
import sys
import time
from pprint import pprint
from random import random

import numpy as np
from animator import Animator
from client import Client
from effect_base import EffectBase
from sim_client import SimClient
from utils import PixelMap, calc_affine, hsl_to_rgb

TARGET_FPS = 1
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
                for z_index in range(0, z):
                    self._game_board[x_index][y_index][z_index] = 0 if random() < 0.8 else 1

    def step(self):
        new_game = self._game_board.copy()
        for x_index in range(0, self._x):
            for y_index in range(0, self._y):
                for z_index in range(0, self._z):
                    ln = self.live_neighbors(x_index, y_index, z_index)
                    if self._game_board[x_index, y_index, z_index] == 1 and ln < 4 or ln > 5:
                        new_game[x_index][y_index][z_index] = 0
                    if self._game_board[x_index, y_index, z_index] == 0 and ln <= 5 and ln >= 5:
                        new_game[x_index][y_index][z_index] = 1
        self._game_board = new_game

    def live_neighbors(self, x, y, z):
        live_count = 0
        for value in self.iter_adjacents(x, y, z):
            live_count = live_count + value
        return live_count

    def iter_adjacents(self, x, y, z):
        gbd = self._game_board.shape
        for x_i in range(x-1, x+2):
            new_x = x_i if x_i >= 0 else gbd[0]-x_i
            new_x = x_i if x_i < gbd[0] else 0
            for y_i in range(y-1, y+2):
                new_y = y_i if y_i >= 0 else gbd[1]-y_i
                new_y = y_i if y_i < gbd[1] else 0
                for z_i in range(z-1, z+2):
                    new_z = z_i if z_i >= 0 else gbd[2]-z_i
                    new_z = z_i if z_i < gbd[2] else 0
                    yield self._game_board[new_x, new_y, new_z]

    def live_cells(self):
        live_cells = np.where(self._game_board == 1)
        if live_cells:
            return zip(live_cells[0], live_cells[1], live_cells[2])
        else:
            return ((), (), ())


class AABB():
    def __init__(self, x_start, x_stop, y_start, y_stop, z_start, z_stop):
        self._x_start = x_start
        self._x_stop = x_stop
        self._y_start = y_start
        self._y_stop = y_stop
        self._z_start = z_start
        self._z_stop = z_stop

    def inside(self, x, y, z):
        return x > self._x_start and x < self._x_stop and \
               y > self._y_start and y < self._y_stop and \
               z > self._z_start and z < self._z_stop

    def contains(self, tup):
        return self.inside(tup[0], tup[1], tup[2])

    def __str__(self):
        return "x: {} -> {} y: {} -> {} z: {} -> {} ".format(self._x_start, self._x_stop, self._y_start, self._y_stop, self._z_start, self._z_stop)

    def __repr__(self):
        return self.__str__()


class ConwaysGameOfLifeEffect(EffectBase):
    def setup(self):
        # Find the extents of the tree
        self.x_min = math.inf
        self.x_max = 0
        self.y_min = math.inf
        self.y_max = 0
        self.z_min = math.inf
        self.z_max = 0

        for pixel in self._map:
            if pixel.coords()[0] > self.x_max:
                self.x_max = pixel.coords()[0]
            if pixel.coords()[0] < self.x_min:
                self.x_min = pixel.coords()[0]
            if pixel.coords()[1] > self.y_max:
                self.y_max = pixel.coords()[1]
            if pixel.coords()[1] < self.y_min:
                self.y_min = pixel.coords()[1]
            if pixel.coords()[2] > self.z_max:
                self.z_max = pixel.coords()[2]
            if pixel.coords()[2] < self.z_min:
                self.z_min = pixel.coords()[2]

        # Add some buffer onto tree extents
        self.x_min = self.x_min - CELL_SIZE
        self.x_max = self.x_max + CELL_SIZE
        self.y_min = self.y_min - CELL_SIZE
        self.y_max = self.y_max + CELL_SIZE
        self.z_min = self.z_min - CELL_SIZE
        self.z_max = self.z_max + CELL_SIZE

        # Build AABB matrix
        self.x_cells = math.ceil((self.x_max - self.x_min) / CELL_SIZE)
        self.y_cells = math.ceil((self.y_max - self.y_min) / CELL_SIZE)
        self.z_cells = math.ceil((self.z_max - self.z_min) / CELL_SIZE)

        self._aabbs = []
        for x_index in range(0, self.x_cells):
            self._aabbs.append([])
            for y_index in range(0, self.y_cells):
                self._aabbs[x_index].append([])
                for z_index in range(0, self.z_cells):
                    self._aabbs[x_index][y_index].append([])
                    self._aabbs[x_index][y_index][z_index] = AABB(
                            self.x_min + (CELL_SIZE * x_index),
                            self.x_min + (CELL_SIZE * (x_index + 1)),
                            self.y_min + (CELL_SIZE * y_index),
                            self.y_min + (CELL_SIZE * (y_index + 1)),
                            self.z_min + (CELL_SIZE * z_index),
                            self.z_min + (CELL_SIZE * (z_index + 1)),
                   )

    def reset(self):
        # Setup internal timer for custom game refresh
        self._timer = 0
        self._visible_live_cells_false_count = 0
        self._live_pixel_history = []
        # Figure out extents of tree
        self._game = GameOfLife3D(self.x_cells, self.y_cells, self.z_cells)

        # Pre-compute the bytes strings for this game round
        hue = random() * 360.0
        red, green, blue = hsl_to_rgb(hue, 1.0, 1.0)
        self._on_pixel = b''.join([
                int(255 * red).to_bytes(1, 'big'),
                int(255 * green).to_bytes(1, 'big'),
                int(255 * blue).to_bytes(1, 'big')
        ])
        self._off_pixel = b''.join([int(0).to_bytes(1, 'big'), int(0).to_bytes(1, 'big'), int(0).to_bytes(1, 'big')])


    def animate(self, delta_t):
        self._timer += delta_t

        # Find the alive aabbs
        alive_aabbs = []
        for cell in self._game.live_cells():
            alive_aabbs.append(self._aabbs[cell[0]][cell[1]][cell[2]])

        # Find which pixels should be active
        live_pixels = []
        pixel_buffer = bytearray()
        for pixel in self._map:
            for aabb in alive_aabbs:
                if aabb.contains(pixel.coords()):
                    pixel_buffer.extend(self._on_pixel)
                    live_pixels.append(pixel.index())
                    break
            else:
                pixel_buffer.extend(self._off_pixel)

        # Step the sim for the next render
        if self._timer > 1:
            self._timer = 0

            # Do some checks to keep things interesting since something could be happening "off screen"
            if len(live_pixels) > 0:
                self._visible_live_cells_false_count = 0
            else:
                self._visible_live_cells_false_count += 1

            self._live_pixel_history.append(live_pixels)
            if len(self._live_pixel_history) > 5:
                self._live_pixel_history.pop(0)
                if all([ph == self._live_pixel_history[0] for ph in self._live_pixel_history]):
                    self._visible_live_cells_false_count = 5


            # Check if this iteration has died out
            if len(list(self._game.live_cells())) <= 0 or self._visible_live_cells_false_count >= 5:
                print("Game dead, resetting")
                self.reset()

            self._game.step()

        return pixel_buffer

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

