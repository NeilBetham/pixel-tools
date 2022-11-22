#!/usr/bin/env python3
import socket
import socketserver

import board
import _rpi_ws281x as ws

PIXEL_COUNT = 500
BYTE_COUNT = PIXEL_COUNT * 3
OFF_FRAME = bytes('00') * BYTE_COUNT

class Pixels():
    def __init__(self, pixel_count, pixel_gpio):
        self._pixel_count = pixel_count
        self._pixel_gpio = pixel_gpio
        self._leds = ws.new_ws2811_t()
        for channum in range(2):
            channel = ws.ws2811_channel_get(self._leds, channum)
            ws.ws2811_channel_t_count_set(channel, 0)
            ws.ws2811_channel_t_gpionum_set(channel, 0)
            ws.ws2811_channel_t_invert_set(channel, 0)
            ws.ws2811_channel_t_brightness_set(channel, 0)

        self._channel = ws.ws2811_channel_get(self._leds, 0)
        ws.ws2811_channel_t_count_set(self._channel, self._pixel_count)
        ws.ws2811_channel_t_gpionum_set(self._channel, self._pixel_gpio)
        ws.ws2811_channel_t_invert_set(self._channel, 0)
        ws.ws2811_channel_t_brightness_set(self._channel, 255)

        ws.ws2811_t_freq_set(self._leds, 800000)
        ws.ws2811_t_dmanum_set(self._leds, 10)

        resp = ws.ws2811_init(self._leds)
        if resp != ws.WS2811_SUCCESS:
            raise RuntimeError("Failed to init LEDs")

    def __del__(self):
        ws.ws2811_fini(self._leds)
        ws.delete_ws2811_t(self._leds)

    def __len__(self):
        return self._pixel_count

    def set_led(self, index, value):
        ws.ws2811_led_set(self._channel, index, value)

    def render(self):
        resp = ws.ws2811_render(self._leds)
        return resp == ws.WS2811_SUCCESS

    def set_frame(self, frame):
        for index in range(len(PIXELS)):
            byte_index = index * 3
            PIXELS.set_led(index, frame[byte_index] << 16 | frame[byte_index + 1] << 8 | frame[byte_index + 2])
        PIXELS.render()


PIXELS = Pixels(PIXEL_COUNT, 18)

class FrameHandler(socketserver.StreamRequestHandler):
    def handle(self):
        frame = self.rfile.read(BYTE_COUNT)
        while len(frame) > 0:
            PIXELS.set_frame(frame)
            self.wfile.write(bytes('true', 'utf-8'))
            frame = self.rfile.read(BYTE_COUNT)
        PIXELS.set_frame(OFF_FRAME)


def main():
    with socketserver.TCPServer(("0.0.0.0", 7689), FrameHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()


