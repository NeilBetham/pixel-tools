#!/usr/bin/env python3

import math
import numpy as np
import os
import socket
import time

from pixel_client import PixelClient

PIXEL_LOCATION_CSV = "pixel_map.filtered.csv"
LOOP_TIME = 1 / 30

class Pixel():
    def __init__(self, index, min_x, max_x, min_y, max_y, min_z, max_z, x, y, z):
        self._index = index
        self._x = x
        self._y = y
        self._z = z
        self._x_n = (x - min_x) / (max_x - min_x)
        self._y_n = (y - min_y) / (max_y - min_y)
        self._z_n = (z - min_z) / (max_z - min_z)

    def coords(self):
        return (self._x, self._y, self._z)

    def normalized_coords(self):
        return (self._x_n, self._y_n, self._z_n)


class PixelMapIter():
    def __init__(self, pixel_map):
        self._pixel_map = pixel_map
        self._current_index = 0
        self._pixel_count = len(self._pixel_map)

    def __iter__(self):
        return self

    def __next__(self):
        if self._current_index < self._pixel_count:
            pixel = self._pixel_map[self._current_index]
            self._current_index += 1
            return pixel
        else:
            raise StopIteration


class PixelMap():
    def __init__(self, pixel_map_csv):
        self._map = {}
        self._pixel_map = {}
        self._current_index = 0
        self._pixel_count = 0
        self._x_min = math.inf
        self._x_max = 0
        self._y_min = math.inf
        self._y_max = 0
        self._z_min = math.inf
        self._z_max = 0

        with open(pixel_map_csv) as pixel_map:
            for line in pixel_map:
                if 'index' in line:
                    continue
                index, x, y, z = line.split(',')
                index = int(index)
                x = int(x)
                y = int(y)
                z = int(z)
                self._map[index] = (x, y, z)
                self._pixel_count += 1

                self._x_min = x if x < self._x_min else self._x_min
                self._x_max = x if x > self._x_max else self._x_max
                self._y_min = y if y < self._y_min else self._y_min
                self._y_max = y if y > self._y_max else self._y_max
                self._z_min = z if z < self._z_min else self._z_min
                self._z_max = z if z > self._z_max else self._z_max

        print(self._x_min, self._x_max, self._y_min, self._y_max, self._z_min, self._z_max)
        for index, pixel in self._map.items():
            self._pixel_map[index] = Pixel(index, self._x_min, self._x_max, self._y_min, self._y_max, self._z_min, self._z_max, pixel[0], pixel[1], pixel[2])

    def __iter__(self):
        return PixelMapIter(self._pixel_map)

    def count(self):
        return self._pixel_count

    def extents(self):
        return (self._x_min, self._x_max, self._y_min, self._y_max, self._z_min, self._z_max)


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

    def animate(self, delta_t):
        # Find our current progress
        self._progress = (self._speed * delta_t) + self._progress
        if self._progress > 1.0:
            self._progress -= 1.0

        buffer = bytearray()
        for pixel in self._map:
            gaussian = self.gaussian(pixel.normalized_coords()[1], self._progress * 1.7 - 1.5)
            intensity_data = self.intensity_data(gaussian)
            buffer.extend(intensity_data)
        return buffer

    def gaussian(self, value, offset):
        return math.e ** (-(value + offset) ** 2 * 300)

    def intensity_data(self, intensity):
        return b''.join([int(255 * intensity).to_bytes(1, 'big'), int(255 * intensity).to_bytes(1, 'big'), int(255 * intensity).to_bytes(1, 'big')])


def main():
    pixel_server = PixelClient()
    pixel_map = PixelMap(os.path.join(os.getcwd(), PIXEL_LOCATION_CSV))
    animator = Animator()
    plane_anim = PlaneWaveEffect(pixel_map, 0.1, 0)
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

