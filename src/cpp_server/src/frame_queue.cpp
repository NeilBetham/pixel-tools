#include "frame_queue.h"


namespace pixel_tools {


void FrameQueue::handle_frame(const std::string& frame) {
  {
    std::lock_guard<std::mutex> lg(_frame_mutex);
    _frames.push_back(frame);
  }
  _new_frame_cv.notify_one();

}

std::string FrameQueue::get_next_frame() {
  std::unique_lock<std::mutex> lock(_frame_mutex);
  _new_frame_cv.wait(lock, [&]{ return _frames.size() > 0; });
  std::string new_frame = _frames.front();
  _frames.pop_front();

  return new_frame;
}


} // namespace pixel_tools
