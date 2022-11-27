#!/usr/bin/env python3

import numpy as np
import os
import socket
import sys
import time
import threading
import signal
from pprint import pprint
from select import select

import trimesh
import pyrender


VIEWER = None
SCENE = None
QUIT = threading.Lock()



def signal_handler(signum, frame):
    print("Exiting...")
    if QUIT.locked():
        QUIT.release()

class TreeSim():
    def __init__(self, pixel_map):
        self._pixel_map = pixel_map
        self._pixel_count = len(self._pixel_map)
        self._scene = pyrender.Scene(ambient_light=[1, 1, 1], bg_color=[0, 0, 0, 0])

        # Compute the normalized location of all the pixels
        self._points = [[pixel[0] / 1080, pixel[1] / 1080, pixel[2] / 1920] for index, pixel in self._pixel_map.items()]
        self._poses = np.tile(np.eye(4), (self._pixel_count, 1, 1))
        self._poses[:,:3,3] = self._points

        # Setup the mesh for each light
        all_on = [[color[0], color[1], color[2]] for color in np.tile(np.ones(3), [self._pixel_count, 1])]
        self._pixel_mesh = pyrender.Mesh.from_points(self._points, colors=all_on)

        pprint(self._pixel_mesh.primitives[0].mode)

        self._pixel_mesh_node = self._scene.add(self._pixel_mesh)


    def update(self, frame):
        if len(frame) != (self._pixel_count * 3):
            return

        # First calculate normalized colors and put them in a matrix
        colors = []
        for index in range(self._pixel_count):
            byte_index = index * 3
            red = frame[byte_index] / 255
            green = frame[byte_index + 1] / 255
            blue = frame[byte_index + 2] / 255
            colors.append([red, green, blue])

        with VIEWER.render_lock:
            self._scene.remove_node(self._pixel_mesh_node)
            self._pixel_mesh = pyrender.Mesh.from_points(self._points, colors=colors)
            self._pixel_mesh_node = self._scene.add(self._pixel_mesh)

    def scene(self):
        return self._scene


class FrameSocketConn():
    def __init__(self, connection):
        self._connection = connection
        self._open = True

    def __del__(self):
        self._connection.close()

    def is_open(self):
        return self._open

    def has_data(self):
        if self._open == False:
            return False
        r, w, x = select([self._connection.fileno()], [], [], 0)
        return self._connection.fileno() in r

    def read_data(self, byte_count):
        if self._open == False:
            return ""
        rx = self._connection.recv(byte_count)
        if len(rx) < 1:
            self._open = False
            return ""
        else:
            return rx


class FrameSocket():
    def __init__(self, socket_path):
        self._socket_path = socket_path
        self._socket = socket.socket(socket.AF_UNIX)
        try:
            self._socket.bind(self._socket_path)
        except:
            os.remove(self._socket_path)
            self._socket.bind(self._socket_path)

    def __del__(self):
        self._socket.close()
        os.remove(self._socket_path)

    def listen(self):
        self._socket.listen()

    def connection_waiting(self):
        r, w, x = select([self._socket.fileno()], [], [], 0)
        return self._socket.fileno() in r

    def accept_connection(self):
        conn, remote = self._socket.accept()
        return FrameSocketConn(conn)


def load_pixel_map(pixel_map_path):
    pixel_map = {}
    with open(pixel_map_path) as pixel_csv:
        for line in pixel_csv:
            if 'index' in line:
                continue
            index, x, y, z, pov1, pov2 = [int(a) for a in line.split(',')]
            pixel_map[index] = (x, y, z, pov1, pov2)

    return pixel_map


def update_loop():
    global VIEWER
    global SCENE
    global QUIT

    print('Update loop started')

    pixel_map_path = sys.argv[1]
    socket_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.getcwd(), "tree_sim.sock")

    pixel_map = load_pixel_map(pixel_map_path)
    tree_sim = TreeSim(pixel_map)
    frame_socket = FrameSocket(socket_path)
    frame_socket.listen()

    expected_bytes = len(pixel_map) * 3
    frame_socket_conns = []
    closed_frame_socket_conns = []

    SCENE = tree_sim.scene()

    while VIEWER is None:
        if not QUIT.locked():
            return
        time.sleep(0.01)

    while QUIT.locked():
        frame = b''
        if frame_socket.connection_waiting():
            frame_socket_conns.append(frame_socket.accept_connection())
        for conn in frame_socket_conns:
            while conn.has_data():
                frame = conn.read_data(expected_bytes)
            if not conn.is_open():
                closed_frame_socket_conns.append(conn)
        for closed_conn in closed_frame_socket_conns:
            frame_socket_conns.remove(closed_conn)
        closed_frame_socket_conns = []

        tree_sim.update(frame)
        if not VIEWER.is_active:
            return
        time.sleep(0.016)

    VIEWER.close_external()


def main():
    global VIEWER
    global SCENE
    global QUIT

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    QUIT.acquire()

    update_thread = threading.Thread(target=update_loop)
    update_thread.start()

    while SCENE is None and QUIT.locked():
        time.sleep(0.01)
    VIEWER = pyrender.Viewer(SCENE, auto_start=False, point_size=10, use_raymond_lighting=True, light_intensity=3000000)
    pprint(VIEWER.render_flags)
    VIEWER.start()
    while VIEWER.is_active:
        time.sleep(0.01)
    if QUIT.locked():
        QUIT.release()
    update_thread.join()

if __name__ == "__main__":
    main()
