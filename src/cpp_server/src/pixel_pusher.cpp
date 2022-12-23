#include "pixel_pusher.h"

#include <chrono>
#include <iostream>
#include <unistd.h>

#include "utils.h"

// defaults for cmdline options
#define TARGET_FREQ             WS2811_TARGET_FREQ
#define GPIO_PIN                18
#define DMA                     10
#define STRIP_TYPE              WS2811_STRIP_RGB
#define LED_COUNT               1000

namespace pixel_tools {


PixelPusher::PixelPusher(FrameQueue& frame_queue) : _frame_queue(frame_queue) {
  _pixels = {
    .freq = TARGET_FREQ,
    .dmanum = DMA,
    .channel = {
        [0] = {
            .gpionum = GPIO_PIN,
            .invert = 0,
            .count = LED_COUNT,
            .strip_type = STRIP_TYPE,
            .brightness = 255,
        },
        [1] = {
            .gpionum = 0,
            .invert = 0,
            .count = 0,
            .brightness = 0,
        },
     },
  };

	ws2811_return_t ret = ws2811_init(&_pixels);
	if(ret != WS2811_SUCCESS) {
		log("Error initing pixels");
		exit(-1);
	}

	_task.set_delegate(this);
}

PixelPusher::~PixelPusher() {
	ws2811_fini(&_pixels);
}

void PixelPusher::run() {
	_task.start();
}

void PixelPusher::stop() {
	_frame_queue.handle_frame(std::string(0));
	_task.stop();
}


void PixelPusher::loop() {
	auto get_frame_start = std::chrono::high_resolution_clock::now();
	auto new_frame = _frame_queue.get_next_frame();
	auto get_frame_stop = std::chrono::high_resolution_clock::now();
	for(int index = 0; index < LED_COUNT; index++) {
		int byte_index = index * 3;
		_pixels.channel[0].leds[index] = ((uint32_t)new_frame[byte_index] << 16) | ((uint32_t)new_frame[byte_index + 1] << 8) | (uint32_t)new_frame[byte_index + 2];
	}
	auto pixel_assign_stop = std::chrono::high_resolution_clock::now();
	ws2811_return_t ret = ws2811_render(&_pixels);
	if(ret != WS2811_SUCCESS) {
		log("Failed to display frame");
		exit(-1);
	}
	auto pixel_render_stop = std::chrono::high_resolution_clock::now();

//	ret = ws2811_wait(&_pixels);
	if(ret != WS2811_SUCCESS) {
		log("Failed to wait for frame to display");
		exit(-1);
	}
	auto pixel_wait_stop = std::chrono::high_resolution_clock::now();

	auto get_time = std::chrono::duration_cast<std::chrono::milliseconds>(get_frame_stop - get_frame_start).count();
	auto assign_time = std::chrono::duration_cast<std::chrono::milliseconds>(pixel_assign_stop - get_frame_stop).count();
	auto render_time = std::chrono::duration_cast<std::chrono::milliseconds>(pixel_render_stop - pixel_assign_stop).count();
	auto wait_time = std::chrono::duration_cast<std::chrono::milliseconds>(pixel_wait_stop - pixel_render_stop).count();

	std::cout << "FG: " << get_time << ", AT: " << assign_time << ", RT: " << render_time << ", WT: " << wait_time << std::endl;

}


} // namespace pixel_tools
