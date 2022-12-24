/**
 * @brief Socket server for displaying frames on a pixel LED string
 */

#include <iostream>
#include <unistd.h>

#include "socket_server.h"
#include "frame_queue.h"
#include "pixel_pusher.h"


int main() {
  std::cout << "Pixel server starting" << std::endl;
  pixel_tools::FrameQueue frame_queue;
  pixel_tools::SocketServer socket_server("0.0.0.0", 7689, frame_queue);
	pixel_tools::PixelPusher pixel_pusher(frame_queue);

	pixel_pusher.run();
  socket_server.run();
  while(true) {
    sleep(1);
  }

}
