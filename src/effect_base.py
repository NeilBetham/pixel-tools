#!/usr/bin/env python3


class EffectBase():
    def __init__(self, pixel_map):
        self._map = pixel_map
        self.reset()
        self._fade_out_timer = 0
        self._fade_out_time = 0
        self._fade_out_active = False
        self._fade_in_timer = 0
        self._fade_in_time = 0
        self._fade_in_active = False

    def animate(self, delta_t):
        # Do all animation related work here, return the byte string to be displayed
        raise NotImplementedError()

    def animate_base(self, delta_t):
        frame = self.animate(delta_t)
        percent = 1.0
        if self._fade_in_active:
            self._fade_in_timer -= delta_t
            percent = 1.0 - (self._fade_in_timer / self._fade_in_time)
            if self._fade_in_timer < 0:
                self._fade_in_active = False

        elif self._fade_out_active:
            self._fade_out_timer -= delta_t
            percent = self._fade_out_timer / self._fade_out_time
            if self._fade_out_timer < 0:
                self._fade_out_active = False

        percent = percent if percent >= 0.0 else 0.0
        percent = percent if percent <= 1.0 else 1.0

        frame = bytearray([int(float(elem) * percent) for elem in frame])
        return frame

    def fade_in(self, time_s):
        if self._fade_in_active:
            return
        # Fade the effect in if it has a fade in
        self._fade_in_timer = time_s
        self._fade_in_time = time_s
        self._fade_in_active = True

    def fade_out(self, time_s):
        if self._fade_out_active:
            return
        #  the effect if this effect has an end
        self._fade_out_timer = time_s
        self._fade_out_time = time_s
        self._fade_out_active = True

    def reset(self):
        # Use this to reset state of effect back to beginning
        pass
