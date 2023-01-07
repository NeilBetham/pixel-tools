#!/usr/bin/env python3

import cv2
import glob
import math
import matplotlib.pyplot as plot
import numpy as np
import os
import pathlib
from pprint import pprint

# Inspiration from https://github.com/standupmaths
# NOTE: This script assumes 4 POVs spaced 90 degress apart by default


CORRECT_DISTANCE_PERCENTAGE = 0.6
AVERAGE_DISTANCE_IN_A_SPHERE = 0.75
BASELINE_AVERAGE_WINDOW = 10


class POVAverager():
    def __init__(self, photos_path):
        self._baselines = []
        self._photos_path = photos_path
        self._photos = []

        for photo in PixelPhotoIter(photos_path):
            self._photos.append(photo)

    def average_at(self, index):
        start_index, stop_index = self._average_indexes_at(index)
        photos_to_average = self._photos[start_index:stop_index]
        average = None
        for photo in photos_to_average:
            if average is None:
                average = photo.frame()
            else:
                float_frame = photo.frame()
                average = (average + float_frame) * 0.5
        return average.clip(min=0, max=255).astype('uint8')

    def _average_indexes_at(self, index):
        start_index = index - (BASELINE_AVERAGE_WINDOW / 2)
        if start_index < 0:
            start_index = 0
        stop_index = start_index + BASELINE_AVERAGE_WINDOW
        if stop_index > (len(self._photos)):
            stop_index = len(self._photos)
            start_index = stop_index - BASELINE_AVERAGE_WINDOW
        return (int(start_index), int(stop_index))


class Photo():
    def __init__(self, photo_path):
        self._path = photo_path

    def frame(self):
        if not hasattr(self, "_frame"):
            self._frame = cv2.imread(self._path, flags=cv2.IMREAD_GRAYSCALE)
        return self._frame

    def color_frame(self):
        if not hasattr(self, "_color_frame"):
            self._color_frame = cv2.imread(self._path)
        return self._color_frame

    def file_name(self):
        return os.path.basename(self._path)

    def path(self):
        return os.path.dirname(self._path)

    def index(self):
        return self.file_name().rsplit(".", 1)[0]

    def extension(self):
        return self.file_name().rsplit(".", 1)[1]

    def output_path(self, subscript):
        return os.path.join(self.path(), self.index() + "." + str(subscript) + "." + self.extension())


class PixelPhotoIter():
    def __init__(self, photos_path):
        self._path = os.path.expanduser(photos_path)
        ret_dir = os.getcwd()
        os.chdir(self._path)
        self._photo_count = len(glob.glob("*[0-9].png"))
        os.chdir(ret_dir)
        self._current_photo = 0

    def __iter__(self):
        return self

    def __next__(self):
        ret_path = os.path.join(self._path, "%i.png" % (self._current_photo))
        ret_index = self._current_photo
        if self._current_photo < self._photo_count:
            self._current_photo += 1
            return Photo(ret_path)
        else:
            raise StopIteration

class POVIter():
    def __init__(self, povs_path):
        self._povs_path = povs_path
        ret_dir = os.getcwd()
        os.chdir(povs_path)
        self._pov_count = len(glob.glob("[0-9]"))
        os.chdir(ret_dir)
        self._current_pov = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._current_pov < self._pov_count:
            cur_pov = self._current_pov
            self._current_pov += 1
            return (cur_pov, os.path.join(self._povs_path, str(cur_pov)))
        else:
            raise StopIteration

class PairIter():
    def __init__(self, items):
        self._items = items
        self._pair_count = len(self._items) - 1
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < self._pair_count:
            current_item = self._items[self._index]
            next_item = self._items[self._index + 1]
            self._index += 1
            return (current_item, next_item)
        else:
            raise StopIteration

def process_photo(pov_averager, index, photo):
    baseline = pov_averager.average_at(index)
    baseline = cv2.rotate(baseline, cv2.ROTATE_90_CLOCKWISE)
    rotated = cv2.rotate(photo.frame(), cv2.ROTATE_90_CLOCKWISE)
    diff = cv2.subtract(rotated, baseline)
    diff_blurred = cv2.GaussianBlur(diff, (11, 11), 0)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(diff_blurred)
    annotated = diff_blurred.copy()
    annotated = cv2.drawMarker(annotated, max_loc, (255, 100, 100), cv2.MARKER_CROSS, thickness=2)
    cv2.imwrite(photo.output_path("base"), baseline)
    cv2.imwrite(photo.output_path("anno"), annotated)
    cv2.imwrite(photo.output_path("diff"), diff_blurred)
    return (max_loc, max_val)

def process_pov(pov_path):
    print("Processing POV: {}".format(pov_path))
    light_centers = []
    normalized_light_centers = []

    # Average all the photos from the POV together to get a baseline
    pov_averager = POVAverager(pov_path)

    print("Calculating POV coordinates")
    # Find all the approximate light centers in each image
    photo_iter = PixelPhotoIter(pov_path)
    for index, photo in enumerate(photo_iter):
        light_center = process_photo(pov_averager, index, photo)
        light_centers.append((int(photo.index()), light_center))

    return light_centers

def localize_pixels(light_centers, base_dimensions):
    povs = len(light_centers)
    pixels = len(light_centers[0])

    pixel_coords = []

    # Pick the two brightest POVs to localize the pixel
    for pixel_index in range(pixels):
        pov1 = -1
        pov1_intensity = -1
        pov2 = -1
        pov2_intensity = -1

        # Find the brightest POV
        for pov in range(povs):
            pixel_map = light_centers[pov][pixel_index]
            if pixel_map[1][1] > pov1_intensity:
                pov1_intensity = pixel_map[1][1]
                pov1 = pov

        # Next check the two neighboring POVs to find which is brightest there
        pov_plus = pov1 + 1
        pov_minus = pov1 - 1

        if pov_plus >= povs:
            pov_plus = 0

        if pov_minus < 0:
            pov_minus = (povs - 1)

        if light_centers[pov_plus][pixel_index][1][1] > light_centers[pov_minus][pixel_index][1][1]:
            pov2 = pov_plus
            pov2_intensity = light_centers[pov_plus][pixel_index][1][1]
        else:
            pov2 = pov_minus
            pov2_intensity = light_centers[pov_minus][pixel_index][1][1]

        # Calc tree frame 3D coord in picture space
        # POV 0 is assumed to be front and the ordering is clockwise around the tree from the top down perspective
        # Image 0,0 is upper left corner
        # TODO: Handle any number of POVs
        xcoord = -1
        ycoord = -1
        zcoord = -1

        if pov1 == 0:
            # This POV is contributing to the X coordinate
            xcoord = light_centers[pov1][pixel_index][1][0][0]
        elif pov1 == 1:
            # This POV is contributing to the Y coordinate
            ycoord = light_centers[pov1][pixel_index][1][0][0]
        elif pov1 == 2:
            # This POV is contributing to the X coordinate in the inverse direction
            xcoord = base_dimensions[0] - light_centers[pov1][pixel_index][1][0][0]
        elif pov1 == 3:
            # This POV is contributing to the Y coordinate in the inverse direction
            ycoord = base_dimensions[0] - light_centers[pov1][pixel_index][1][0][0]

        if pov2 == 0:
            # This POV is contributing to the X coordinate
            xcoord = light_centers[pov2][pixel_index][1][0][0]
        elif pov2 == 1:
            # This POV is contributing to the Y coordinate
            ycoord = light_centers[pov2][pixel_index][1][0][0]
        elif pov2 == 2:
            # This POV is contributing to the X coordinate in the inverse direction
            xcoord = base_dimensions[0] - light_centers[pov2][pixel_index][1][0][0]
        elif pov2 == 3:
            # This POV is contributing to the Y coordinate in the inverse direction
            ycoord = base_dimensions[0] - light_centers[pov2][pixel_index][1][0][0]

        zcoord = (light_centers[pov1][pixel_index][1][0][1] + light_centers[pov2][pixel_index][1][0][1]) / 2
        zcoord = base_dimensions[1] - zcoord

        pixel_coords.append((pixel_index, (xcoord, ycoord, zcoord, pov1, pov2)))

    return pixel_coords


def normalize_map(pixel_coords):
    min_x = math.inf
    max_x = 0.0
    min_y = math.inf
    max_y = 0.0
    min_z = math.inf
    max_z = 0.0

    for coord in pixel_coords:
        x = coord[1][0]
        y = coord[1][1]
        z = coord[1][2]
        if x < min_x:
            min_x = x
        if x > max_x:
            max_x = x
        if y < min_y:
            min_y = y
        if y > max_y:
            max_y = y
        if z < min_z:
            min_z = z
        if z > max_z:
            max_z = z

    min_coord = float(min_x if min_x < min_y else min_y)
    max_coord = float(max_x if max_x > max_y else max_y)
    coord_range = max_coord - min_coord
    half_coord_range = coord_range / 2.0
    mid_coord = half_coord_range + min_coord
    mid_coord_x = (max_x - min_x) / 2 + min_x
    mid_coord_y = (max_y - min_y) / 2 + min_y

    normal_pixel_coords = []
    for coord in pixel_coords:
        norm_x = (float(coord[1][0]) - mid_coord_x) / half_coord_range
        norm_y = (float(coord[1][1]) - mid_coord_y) / half_coord_range
        norm_z = (float(coord[1][2]) - mid_coord) / half_coord_range

        normal_pixel_coords.append((coord[0], (norm_x, norm_y, norm_z, coord[1][3], coord[1][4])))

    return normal_pixel_coords


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
    x = [coord[1][0] for coord in pixel_coords]
    y = [coord[1][1] for coord in pixel_coords]
    z = [coord[1][2] for coord in pixel_coords]
    axes.scatter(x, y, z)
    axes.set_title('Pixel Map')
    plot.show()


def pixel_coord_correction(pixel_coords):
    pixel_pair_iter = PairIter(pixel_coords)
    distance_list = []

    # First find the distance beteen all pixels
    for item1, item2 in pixel_pair_iter:
        x_dist = (item2[1][0] - item1[1][0])**2
        y_dist = (item2[1][1] - item1[1][1])**2
        z_dist = (item2[1][2] - item1[1][2])**2
        pyth_dist = (x_dist + y_dist + z_dist)**0.5
        distance_list.append(((item1[0], item2[0]), pyth_dist))

    distance_list_sorted = distance_list[::]
    distance_list_sorted.sort(key=lambda a: a[1])

    # Get some user input as to what we should use for the percentage of correct distances
    print("You will need to choose what percentage of LED distances are correct.")
    print("Please look at the graph presented after you hit enter and then")
    print("a percetnage as a decimal between 0 and 1.")
    input("Press enter when ready...")
    plot_pixel_distances(distance_list_sorted)
    CORRECT_DISTANCE_PERCENTAGE = float(input("What percentage is correct: "))

    # Find the max allowable distance between pixels
    average_correct = 0
    correct_count = int(len(distance_list_sorted) * CORRECT_DISTANCE_PERCENTAGE)
    for index in range(correct_count):
        average_correct += distance_list_sorted[index][1]
    average_correct /= correct_count
    max_distance = average_correct / AVERAGE_DISTANCE_IN_A_SPHERE

    # Sort gaps based on distance over or under max_distance
    distance_list_binned = []
    for distance in distance_list:
        if distance[1] <= max_distance:
            distance_list_binned.append((True, distance))
        else:
            distance_list_binned.append((False, distance))

    # Filter the gaps in the original string based on number of links
    # There must be more than two LEDs connected correctly for the segment to be considered correct
    distance_list_filtered = []
    for index, distance in enumerate(distance_list_binned):
        if index > 0 and index < (len(distance_list_binned) - 1) and distance_list_binned[index - 1][0] != True and distance_list_binned[index + 1][0] != True:
            distance_list_filtered.append((False, distance[1]))
        else:
            distance_list_filtered.append(distance)

    # Start build a list of gaps to fix
    gaps_to_fix = []
    gap_start = -1
    for index, distance in enumerate(distance_list_filtered):
        if gap_start == -1 and distance[0] is False:
            gap_start = distance[1][0][0]
        if gap_start != -1 and distance[0] is True:
            gaps_to_fix.append((gap_start, distance_list_filtered[index - 1][1][0][1]))
            gap_start = -1

    # Next string the badly localized pixels along in between good ones
    fixed_pixels = []
    for pixel_coord in pixel_coords:
        for gap in gaps_to_fix:
            if pixel_coord[0] in range(gap[0], gap[1]):
                gap_length = gap[1] - gap[0]
                index_in_gap = pixel_coord[0] - gap[0]
                gap_percentage = index_in_gap / gap_length
                gap_start = np.array(pixel_coords[gap[0]][1][0:3])
                gap_end = np.array(pixel_coords[gap[1]][1][0:3])
                gap_diff = (gap_end - gap_start) * gap_percentage
                coord_new = gap_start + gap_diff
                fixed_pixels.append((pixel_coord[0], tuple(coord_new) + tuple([pixel_coord[1][3], pixel_coord[1][4]])))
                break
        if len(fixed_pixels) <= pixel_coord[0]:
            fixed_pixels.append(pixel_coord)

    return fixed_pixels


def output_pixel_map_csv(pixel_coords, outfile_name):
    outfile = open(outfile_name, 'w')
    outfile.write("index, x, y, z, pov1, pov2\n")
    for pixel_coord in pixel_coords:
        outfile.write("%i, %f, %f, %f, %i, %i\n" % (pixel_coord[0], pixel_coord[1][0], pixel_coord[1][1], pixel_coord[1][2], pixel_coord[1][3], pixel_coord[1][4]))
    outfile.close()


def main():
    pov_iter = POVIter(os.path.join(os.getcwd(), "pixel_maps"))
    pov_maps = {}
    base_image_dimensions = None

    for index, pov_path in pov_iter:
        if base_image_dimensions is None:
            base_image_dimensions = PixelPhotoIter(pov_path).__next__().frame().shape
        pov_maps[index] = process_pov(pov_path)

    pixel_coords = localize_pixels(pov_maps, base_image_dimensions)
    plot_pixel_coords(pixel_coords)
    output_pixel_map_csv(normalize_map(pixel_coords), os.path.join(os.getcwd(), "pixel_map.raw.csv"))
    pixel_coords = pixel_coord_correction(pixel_coords)
    plot_pixel_coords(pixel_coords)
    output_pixel_map_csv(normalize_map(pixel_coords), os.path.join(os.getcwd(), "pixel_map.filtered.csv"))


if __name__ == "__main__":
    main()
