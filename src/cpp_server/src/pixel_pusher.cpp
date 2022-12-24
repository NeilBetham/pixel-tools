#include "pixel_pusher.h"

#include <chrono>
#include <iostream>
#include <unistd.h>

#include "mailbox.h"
#include "clk.h"
#include "gpio.h"
#include "dma.h"
#include "pwm.h"
#include "pcm.h"
#include "rpihw.h"

#define FMT_HEADER_ONLY
#include <fmt/core.h>
#include <string>

#include "utils.h"

// defaults for cmdline options
#define TARGET_FREQ             WS2811_TARGET_FREQ
#define GPIO_PIN                18
#define DMA                     10
#define STRIP_TYPE              WS2811_STRIP_RGB
#define LED_COUNT               1000

// -----------------------------------------------------------------------
// Copy Pasta to enable stripping down / instrumenting the render function
// -----------------------------------------------------------------------
#define BUS_TO_PHYS(x)                           ((x)&~0xC0000000)

#define OSC_FREQ                                 19200000   // crystal frequency
#define OSC_FREQ_PI4                             54000000   // Pi 4 crystal frequency

/* 4 colors (R, G, B + W), 8 bits per byte, 3 symbols per bit + 55uS low for reset signal */
#define LED_COLOURS                              3
#define LED_RESET_uS                             55
#define LED_BIT_COUNT(leds, freq)                ((leds * LED_COLOURS * 8 * 3) + ((LED_RESET_uS * \
                                                  (freq * 3)) / 1000000))

/* Minimum time to wait for reset to occur in microseconds. */
#define LED_RESET_WAIT_TIME                      60

// Pad out to the nearest uint32 + 32-bits for idle low/high times the number of channels
#define PWM_BYTE_COUNT(leds, freq)               (((((LED_BIT_COUNT(leds, freq) >> 3) & ~0x7) + 4) + 4) * \
                                                  RPI_PWM_CHANNELS)
// Symbol definitions
#define SYMBOL_HIGH                              0x6  // 1 1 0
#define SYMBOL_LOW                               0x4  // 1 0 0

// Symbol definitions for software inversion (PCM and SPI only)
#define SYMBOL_HIGH_INV                          0x1  // 0 0 1
#define SYMBOL_LOW_INV                           0x3  // 0 1 1

// Driver mode definitions
#define NONE	0
#define PWM	1
#define PCM	2
#define SPI	3

// We use the mailbox interface to request memory from the VideoCore.
// This lets us request one physically contiguous chunk, find its
// physical address, and map it 'uncached' so that writes from this
// code are immediately visible to the DMA controller.  This struct
// holds data relevant to the mailbox interface.
typedef struct videocore_mbox {
    int handle;             /* From mbox_open() */
    unsigned mem_ref;       /* From mem_alloc() */
    unsigned bus_addr;      /* From mem_lock() */
    unsigned size;          /* Size of allocation */
    uint8_t *virt_addr;     /* From mapmem() */
} videocore_mbox_t;

typedef struct ws2811_device
{
    int driver_mode;
    volatile uint8_t *pxl_raw;
    volatile dma_t *dma;
    volatile pwm_t *pwm;
    volatile pcm_t *pcm;
    int spi_fd;
    volatile dma_cb_t *dma_cb;
    uint32_t dma_cb_addr;
    volatile gpio_t *gpio;
    volatile cm_clk_t *cm_clk;
    videocore_mbox_t mbox;
    int max_count;
} ws2811_device_t;


namespace pixel_tools {

static uint32_t symbol_lookup_table[256] = {0};
void compute_symbol_lookup_table() {
  for(uint16_t index = 0; index < 256; index++) {
    uint32_t out_symbol = 0;
    for(uint8_t bit_index = 0; bit_index < 8; bit_index++) {
      if(index & (1 << bit_index)) {
        out_symbol |= 1 << (bit_index * 3 + 1);
        out_symbol |= 1 << (bit_index * 3 + 2);
      } else {
        out_symbol |= 1 << (bit_index * 3 + 2);
      }
    }

    symbol_lookup_table[index] = out_symbol;
  }
}

void* cpymem(void* dest, void* src, uint32_t size) {
  uint8_t* dest_bytes = (uint8_t*)dest;
  uint8_t* src_bytes = (uint8_t*)src;
  for(uint32_t index = 0; index < size; index++) {
    uint32_t dest_index = size - index - 1;
    dest_bytes[dest_index] = src_bytes[index];
  }
  return dest;
}

static void dma_start_custom(ws2811_t *ws2811) {
  ws2811_device_t *device = ws2811->device;
  volatile dma_t *dma = device->dma;
  uint32_t dma_cb_addr = device->dma_cb_addr;
  volatile dma_cb_t *dma_cb = device->dma_cb;

  dma->cs = RPI_DMA_CS_RESET;
  usleep(10);

  dma->cs = RPI_DMA_CS_INT | RPI_DMA_CS_END;
  usleep(10);

  dma_cb->txfr_len = PWM_BYTE_COUNT(ws2811->channel[0].count, ws2811->freq);

  dma->conblk_ad = dma_cb_addr;
  dma->debug = 7; // clear debug error flags
  dma->cs = RPI_DMA_CS_WAIT_OUTSTANDING_WRITES |
            RPI_DMA_CS_PANIC_PRIORITY(0) |
            RPI_DMA_CS_PRIORITY(0) |
            RPI_DMA_CS_ACTIVE;
}

static ws2811_return_t ws2811_wait_custom(ws2811_t *ws2811) {
	volatile dma_t *dma = ws2811->device->dma;

	while ((dma->cs & RPI_DMA_CS_ACTIVE) && !(dma->cs & RPI_DMA_CS_ERROR)) {
	  usleep(10);
  }

	if (dma->cs & RPI_DMA_CS_ERROR) {
		fprintf(stderr, "DMA Error: %08x\n", dma->debug);
		return WS2811_ERROR_DMA;
	}

	return WS2811_SUCCESS;
}

static ws2811_return_t ws2811_render_custom(ws2811_t *ws2811) {
	volatile uint8_t *pxl_raw = ws2811->device->pxl_raw;
	ws2811_return_t ret = WS2811_SUCCESS;

	for (uint8_t channel_index = 0; channel_index < 1; channel_index++) {
		ws2811_channel_t *channel = &ws2811->channel[channel_index];
		uint8_t color_channels = 3; // Assume 3 color LEDs, RGB

    // Symbol processing state
    uint8_t buffer[12] = {0};
    uint8_t symbols_in_buffer = 0;
    uint32_t outbuffer_byte_pos = 0;


		for (uint32_t led_index = 0; led_index < (uint32_t)channel->count; led_index++) {
			uint8_t color[] = {
				(uint8_t)((channel->leds[led_index] >> channel->rshift) & 0xff), // red
				(uint8_t)((channel->leds[led_index] >> channel->gshift) & 0xff), // green
				(uint8_t)((channel->leds[led_index] >> channel->bshift) & 0xff), // blue
			};

      // Accumulate symbols and them add them to the output buffer
			for (uint8_t color_index = 0; color_index < color_channels; color_index++) {
        uint32_t symbol = symbol_lookup_table[color[color_index]];
        uint8_t buffer_pos = symbols_in_buffer * 3;
        cpymem(&buffer[buffer_pos], &symbol, 3);
        symbols_in_buffer++;

        if(symbols_in_buffer == 4) {
          // Copy over each word into output buffer
          cpymem(&((uint8_t*)pxl_raw)[outbuffer_byte_pos], &buffer[0], 4);
          outbuffer_byte_pos += 8;
          cpymem(&((uint8_t*)pxl_raw)[outbuffer_byte_pos], &buffer[4], 4);
          outbuffer_byte_pos += 8;
          cpymem(&((uint8_t*)pxl_raw)[outbuffer_byte_pos], &buffer[8], 4);
          outbuffer_byte_pos += 8;
          symbols_in_buffer = 0;
          memset(&buffer[0], 0, sizeof(buffer));
        }
		  }
		}

    // Copy over any stragglers into output buffer
    uint8_t* outbuffer_ptr = &((uint8_t*)pxl_raw)[outbuffer_byte_pos];
    memcpy(outbuffer_ptr, &buffer[0], 4);
    outbuffer_ptr += 8;
    memcpy(outbuffer_ptr, &buffer[4], 4);
    outbuffer_ptr += 8;
    memcpy(outbuffer_ptr, &buffer[8], 4);
    outbuffer_byte_pos += 24;
	}

	dma_start_custom(ws2811);

	return ret;
}


PixelPusher::PixelPusher(FrameQueue& frame_queue) : _frame_queue(frame_queue) {
  _pixels = {
    .render_wait_time = 0,
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

  compute_symbol_lookup_table();
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
	auto new_frame = _frame_queue.get_next_frame();
  if(new_frame.size() == 0) {
    clear();
  } else {
    render_frame(new_frame);
  }
}

void PixelPusher::clear() {
  std::string off(_pixels.channel[0].count * 3, 0);
  render_frame(off);
}

void PixelPusher::render_frame(const std::string& frame) {
	for(int index = 0; index < LED_COUNT; index++) {
		int byte_index = index * 3;
		_pixels.channel[0].leds[index] = ((uint32_t)frame[byte_index] << 16) | ((uint32_t)frame[byte_index + 1] << 8) | (uint32_t)frame[byte_index + 2];
	}
	ws2811_return_t ret = ws2811_render_custom(&_pixels);
	if(ret != WS2811_SUCCESS) {
		log("Failed to display frame");
		exit(-1);
	}

  ret = ws2811_wait_custom(&_pixels);
	if(ret != WS2811_SUCCESS) {
		log("Failed to wait for frame to display");
		exit(-1);
	}
}


} // namespace pixel_tools
