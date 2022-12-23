/**
 * @brief Delegate ABS for SocketServer
 */

#include <string>

#pragma once

namespace pixel_tools {


class SocketServerDelegate {
public:
  ~SocketServerDelegate() {};

  virtual void handle_frame(const std::string& frame) = 0;
};


} // namespace pixel_tools
