/**
 * @biref Manages a socket to receive pixel frames
 */

#include <vector>
#include <tuple>

#include "socket_server_delegate.h"
#include "task.h"

#pragma once

namespace pixel_tools {


class SocketServer : public TaskDelegate {
public:
  SocketServer(const std::string& listen_addr, uint16_t port, SocketServerDelegate& delegate): _listen_addr(listen_addr), _port(port), _delegate(delegate) {};
  ~SocketServer();

  void run();
  void stop();

private:
  std::string _listen_addr;
  uint16_t _port;
  SocketServerDelegate& _delegate;
  int _listen_fd = -1;
  int _current_src_fd = -1;
  Task _task;

  void setup_socket();
  void teardown_socket();

  void loop();

  std::tuple<std::vector<int>, std::vector<int>, std::vector<int>> int_select(const std::vector<int>& read_fds, const std::vector<int>& write_fds, const std::vector<int>& error_fds);
};



} // namespace pixel_tools
