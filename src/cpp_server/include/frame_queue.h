/**
 * @brief A thread safe queue for frames
 */

#include <condition_variable>
#include <mutex>
#include <string>
#include <list>

#include "socket_server_delegate.h"


#pragma once

namespace pixel_tools {


class FrameQueue : public SocketServerDelegate {
public:
  void handle_frame(const std::string& frame);

  std::string get_next_frame();


private:
  std::list<std::string> _frames;
  std::mutex _frame_mutex;
  std::mutex _new_frame_lock;
  std::condition_variable _new_frame_cv;

};


} // namespace pixel_tools
