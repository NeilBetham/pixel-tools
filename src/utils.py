#!/usr/bin/env python3

import math
import numpy as np


def calc_affine(rot_x, rot_y, rot_z):
    base_x = np.eye(4)
    base_y = np.eye(4)
    base_z = np.eye(4)

    sin_x = math.sin(rot_x)
    sin_y = math.sin(rot_y)
    sin_z = math.sin(rot_z)

    cos_x = math.cos(rot_x)
    cos_y = math.cos(rot_y)
    cos_z = math.cos(rot_z)

    base_x[1][1] = cos_x
    base_x[1][2] = -sin_x
    base_x[2][1] = sin_x
    base_x[2][2] = cos_x

    base_y[0][0] = cos_y
    base_y[0][2] = sin_y
    base_y[2][0] = -sin_y
    base_y[2][2] = cos_y

    base_z[0][0] = cos_z
    base_z[0][1] = -sin_z
    base_z[1][0] = sin_z
    base_z[1][1] = cos_z

    return np.matmul(np.matmul(base_x, base_y), base_z)

def calc_affine2(rot_x, rot_y, rot_z, t_x, t_y, t_z):
    rot_mat = calc_affine(rot_x, rot_y, rot_z)
    rot_mat[0][3] = t_x
    rot_mat[1][3] = t_y
    rot_mat[2][3] = t_z

    return rot_mat


def hsl_to_rgb(hue, saturation, lightness):
    hue = float(hue)
    saturation = float(saturation)
    lightness = float(lightness)
    chroma = lightness * saturation
    hue_prime = math.fmod(hue / 60.0, 6.0)
    x = chroma * (1.0 - math.fabs(math.fmod(hue_prime, 2.0) - 1.0))
    m = lightness - chroma
    r = 0
    g = 0
    b = 0

    hue_index = int(hue_prime)

    if hue_index == 0:
        r = chroma
        g = x
        b = 0
    elif hue_index == 1:
        r = x
        g = chroma
        b = 0
    elif hue_index == 2:
        r = 0
        g = chroma
        b = x
    elif hue_index == 3:
        r = 0
        g = x
        b = chroma
    elif hue_index == 4:
        r = x
        g = 0
        b = chroma
    elif hue_index == 5:
        r = chroma
        g = 0
        b = x

    r += m
    g += m
    b += m

    return (r, g, b)


class Pixel():
    def __init__(self, index, x, y, z):
        self._index = index
        self._x = x
        self._y = y
        self._z = z

    def coords(self):
        return (self._x, self._y, self._z)

    def index(self):
        return self._index


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
    def __init__(self, pixel_dict):
        self._map = pixel_dict
        self._pixel_map = {}
        self._pixel_count = len(self._map)
        self._pixel_mat = []
        for index, pixel in self._map.items():
            self._pixel_map[index] = Pixel(index, pixel[0], pixel[1], pixel[2])
            self._pixel_mat.append([pixel[0], pixel[1], pixel[2], 1])

    def __iter__(self):
        return PixelMapIter(self._pixel_map)

    @classmethod
    def from_csv(cls, pixel_map_csv):
        pixel_dict = {}
        with open(pixel_map_csv) as pixel_map:
            for line in pixel_map:
                if 'index' in line:
                    continue
                index, x, y, z, pov1, pov2 = line.split(',')
                index = int(index)
                x = float(x)
                y = float(y)
                z = float(z)

                pixel_dict[index] = (x, y, z)
        return PixelMap(pixel_dict)


    def count(self):
        return self._pixel_count

    def mat(self):
        return self._pixel_mat

    def transform(self, transform_mat):
        new_pixel_dict = {}
        for index, coord in enumerate(self._pixel_mat):
            x, y, z, dc =  np.matmul(transform_mat, coord)
            new_pixel_dict[index] = (x, y, z)

        return PixelMap(new_pixel_dict)

