/**
 * @brief General utilities
 */

#include <iostream>
#include <string>

#pragma once

namespace pixel_tools {


static void log(const std::string& message) {
  std::cerr << message << std::endl;
}


} // namespace pixel_tools
