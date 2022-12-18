#!/usr/bin/env python3

import importlib
import os
import sys
import time
from glob import glob
from random import random, choice

from animator import Animator
from client import Client
from sim_client import SimClient
from utils import PixelMap

TARGET_FPS = 30
MIN_EFFECT_TIME = 30
MAX_EFFECT_TIME = 300
FADE_EFFECT_TIME = 5

class Coordinator():
    def __init__(self, pixel_sink, pixel_map):
        self._pixel_sink = pixel_sink
        self._pixel_map = pixel_map
        self._effect_pool = {}
        self._animator = Animator(TARGET_FPS)
        self._effect_timer = 0
        self._current_effect = None
        self._last_effect = None

        self.load_effects()

        self._animator.set_pixel_target(self._pixel_sink)

    def load_effects(self):
        effects_path = os.path.join(os.path.dirname(__file__), 'effects')
        effect_sources = glob(os.path.join(effects_path, '*.py'))
        for effect_source in effect_sources:
            effect_module = os.path.basename(effect_source).rstrip('.py')
            effect_name = effect_module.title().replace('_', '') + 'Effect'
            if effect_name == "InitEffect":
                continue

            print('Loading effect: {}'.format(effect_name))
            effect_module_import = importlib.import_module('.{}'.format(effect_module), 'effects')
            if hasattr(effect_module_import, effect_name):
                self._effect_pool[effect_name] = getattr(effect_module_import, effect_name)(self._pixel_map)
            else:
                print("Ignoring effect due to errors: {}.py".format(effect_module))

    def run(self):
        while True:
            start_time = time.time()
            self._animator.run()
            stop_time = time.time()
            delta_t = stop_time - start_time
            self._effect_timer -= delta_t

            if self._effect_timer < FADE_EFFECT_TIME and self._current_effect:
                self._current_effect.fade_out(FADE_EFFECT_TIME)

            if self._effect_timer < 0:
                self._last_effect = self._current_effect
                self._effect_timer = random() * MAX_EFFECT_TIME
                self._effect_timer = max([self._effect_timer, MIN_EFFECT_TIME])

                while self._current_effect == self._last_effect:
                    chosen_effect = choice(list(self._effect_pool.keys()))
                    self._current_effect = self._effect_pool[chosen_effect]

                self._current_effect.reset()
                self._current_effect.fade_in(FADE_EFFECT_TIME)
                self._animator.set_animator_target(self._current_effect)
                print("Next effect is {} for {} seconds".format(chosen_effect, self._effect_timer))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'sim':
        pixel_server = SimClient('./tree_sim.sock')
    else:
        pixel_server = Client()

    pixel_map = PixelMap.from_csv(os.getenv('PIXEL_MAP_CSV'))

    coordinator = Coordinator(pixel_server, pixel_map)

    coordinator.run()

if __name__ == "__main__":
    main()
