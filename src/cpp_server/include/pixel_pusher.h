/**
 * @brief Responsible for pushing frames out to pixels
 */

#include "ws2811.h"


#include "frame_queue.h"
#include "task.h"


#pragma once

namespace pixel_tools {


class PixelPusher : public TaskDelegate {
public:
  PixelPusher(FrameQueue& frame_queue);
  ~PixelPusher();

  void run();
  void stop();

  void loop();

private:
  FrameQueue& _frame_queue;
  Task _task;
  ws2811_t _pixels;
};


}
