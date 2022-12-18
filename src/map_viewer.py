#!/usr/bin/env python3

import sys
from pprint import pprint

import matplotlib.pyplot as plot
import numpy as np


def plot_pixel_distances(pixel_distances):
    distances = [dist[1] for dist in pixel_distances]
    distances.sort()
    figure = plot.figure()
    plot.bar(range(len(distances)), distances)
    plot.ylabel('Distance')
    plot.title('Distance between pixel pairs')
    plot.show()

def plot_pixel_coords(pixel_coords):
    figure = plot.figure()
    axes = plot.axes(projection = '3d')
    x = [coord[0] for index, coord in pixel_coords.items()]
    y = [coord[1] for index, coord in pixel_coords.items()]
    z = [coord[2] for index, coord in pixel_coords.items()]
    pov_index =  [int("{}{}".format(coord[3], coord[4])) for index, coord in pixel_coords.items()]
    pprint(set(pov_index))
    axes.scatter(x, y, z, c=pov_index, cmap='hsv')
    axes.set_title('Pixel Map')
    plot.show()

def main():
    map_file = sys.argv[1]
    pixel_map_dict = {}


    with open(map_file) as pixel_map:
        for line in pixel_map:
            if "index" in line:
                continue
            index, x, y, z, pov1, pov2 = line.split(',')
            pixel_map_dict[index] = (int(x), int(y), int(z), int(pov1), int(pov2))

    plot_pixel_coords(pixel_map_dict)


if __name__ == "__main__":
    main()
