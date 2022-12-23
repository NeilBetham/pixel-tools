/**
 * @brief ABS for Task delegate
 */

#pragma once

namespace pixel_tools {


class TaskDelegate {
public:
  ~TaskDelegate() {};

  virtual void loop() = 0;
};


} // namespace pixel_tools
