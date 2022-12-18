#!/usr/bin/env python3

import time

class Animator():
    def __init__(self, fps):
        self._last_anim_exec = time.time()
        self._anim_target = None
        self._pixel_target = None
        self._loop_time = 1 / fps

    def animate(self):
        start_time = time.time()
        if self._anim_target:
            pixel_bytes = self._anim_target.animate_base(start_time - self._last_anim_exec)
            if self._pixel_target:
                self._pixel_target.send_frame(pixel_bytes)
        self._last_anim_exec = start_time

    def set_animator_target(self, target):
        self._anim_target = target

    def set_pixel_target(self, target):
        self._pixel_target = target

    def run(self):
        # Fist check how long we need to sleep to maintain framerate
        stop_time = time.time()
        delta_t = stop_time - self._last_anim_exec
        sleep_time = self._loop_time - delta_t
        if sleep_time > 0:
            time.sleep(sleep_time)

        # Start the next animation run
        self.animate()

