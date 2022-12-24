#include "socket_server.h"

#include <arpa/inet.h>
#include <iterator>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <stdio.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <unistd.h>

#include "utils.h"

namespace pixel_tools {

constexpr uint32_t PIXEL_COUNT = 1000;
constexpr uint32_t PIXEL_BUFFER_SIZE = PIXEL_COUNT * 3;


bool present(const std::vector<int>& fds, int fd) {
  for(const auto& check_fd : fds) {
    if(check_fd == fd) {
      return true;
    }
  }

  return false;
}


SocketServer::~SocketServer() {
  _task.stop();
  teardown_socket();
}

void SocketServer::run() {
  setup_socket();
  _task.set_delegate(this);
  _task.start();
}

void SocketServer::stop() {
  _task.stop();
  teardown_socket();
}

void SocketServer::setup_socket() {
  _listen_fd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);
  if(_listen_fd == -1) {
    log("Error creating listen socket");
    perror("socket");
    exit(-1);
  }

  int dnc = 1;
  int set_sock_res = setsockopt(_listen_fd, IPPROTO_TCP, TCP_NODELAY, &dnc, sizeof(dnc));
  if(set_sock_res != 0) {
    log("Failed to set TCP_NODELAY");
    perror("setsockopt");
    exit(-1);
  }

  int set_sock_res2 = setsockopt(_listen_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &dnc, sizeof(dnc));
  if(set_sock_res2 != 0) {
    log("Failed to set RESUE flags");
    perror("setsockopt");
    exit(-1);
  }

  struct sockaddr_in listen_address;
  listen_address.sin_family = AF_INET;
  listen_address.sin_port = htons(_port);

  int conv_res = inet_aton(_listen_addr.c_str(), &listen_address.sin_addr);
  if(conv_res == 0) {
    log("Error converting listen IP to bin");
    perror("inet_aton");
    exit(-1);
  }

  int bind_res = bind(_listen_fd, (const sockaddr*)&listen_address, sizeof(listen_address));
  if(bind_res != 0) {
    log("Error binding to listen address");
    perror("bind");
    exit(-1);
  }

  int listen_res = listen(_listen_fd, 10);
  if(listen_res != 0) {
    log("Failed to set listen mode on socket");
    perror("listen");
    exit(-1);
  }
}

void SocketServer::teardown_socket() {
  close(_listen_fd);
  close(_current_src_fd);
}

void SocketServer::loop() {
  // First we wait for a new connection
  std::vector<int> read_fds = {_listen_fd, _task.ping_fd()};
  if(_current_src_fd != -1) {
    read_fds.push_back(_current_src_fd);
  }

  std::vector<int> readable_fds;
  std::vector<int> writeable_fds;
  std::vector<int> error_fds;
  std::tie(readable_fds, writeable_fds, error_fds) = int_select(read_fds, {}, {});

  if(present(readable_fds, _task.ping_fd())) {
    return;
  }

  if(present(readable_fds, _current_src_fd)) {
    uint8_t buffer[PIXEL_BUFFER_SIZE] = {0};

    // Read until we have a full buffer
    uint32_t read_bytes = 0;
    while(read_bytes < PIXEL_BUFFER_SIZE) {
      uint32_t recv_bytes = read(_current_src_fd, buffer + read_bytes, PIXEL_BUFFER_SIZE - read_bytes);
      if(recv_bytes < 1) {
        close(_current_src_fd);
        _current_src_fd = -1;
        _delegate.handle_frame(std::string());
        return;
      }
      read_bytes += recv_bytes;
    }


    if(read_bytes == PIXEL_BUFFER_SIZE) {
      _delegate.handle_frame(std::string((char*)&buffer, PIXEL_BUFFER_SIZE));
      std::string resp_buffer("true");
      write(_current_src_fd, resp_buffer.c_str(), 4);
    }
  }

  if(present(readable_fds, _listen_fd)) {
    // Accept a connection if we don't have one already
    int src_fd = accept(_listen_fd, NULL, NULL);
    if(src_fd != -1) {
      if(_current_src_fd == -1) {
        _current_src_fd = src_fd;
      } else {
        close(src_fd);
      }
    } else {
      log("Accept was readable but returned error");
      perror("accept");
      exit(-1);
    }
  }
}

std::tuple<std::vector<int>, std::vector<int>, std::vector<int>> SocketServer::int_select(const std::vector<int>& read_fds, const std::vector<int>& write_fds, const std::vector<int>& error_fds) {
  std::vector<int> set_read_fds;
  std::vector<int> set_write_fds;
  std::vector<int> set_error_fds;

  int highest_fd = -1;
  fd_set read_fd_set;
  fd_set write_fd_set;
  fd_set error_fd_set;

  FD_ZERO(&read_fd_set);
  FD_ZERO(&write_fd_set);
  FD_ZERO(&error_fd_set);

  for(const auto& fd : read_fds) {
    FD_SET(fd, &read_fd_set);
    if(fd > highest_fd) {
      highest_fd = fd;
    }
  }

  for(const auto& fd : write_fds) {
    FD_SET(fd, &write_fd_set);
    if(fd > highest_fd) {
      highest_fd = fd;
    }
  }
  for(const auto& fd : error_fds) {
    FD_SET(fd, &error_fd_set);
    if(fd > highest_fd) {
      highest_fd = fd;
    }
  }

  int sel_res = select(highest_fd + 1, &read_fd_set, &write_fd_set, &error_fd_set, NULL);
  if(sel_res < 1) {
    return std::make_tuple<std::vector<int>, std::vector<int>, std::vector<int>>({}, {}, {});
  }

  for(const auto& fd : read_fds) {
    if(FD_ISSET(fd, &read_fd_set)) {
      set_read_fds.push_back(fd);
    }
  }
  for(const auto& fd : write_fds) {
    if(FD_ISSET(fd, &write_fd_set)) {
      set_write_fds.push_back(fd);
    }
  }
  for(const auto& fd : error_fds) {
    if(FD_ISSET(fd, &error_fd_set)) {
      set_error_fds.push_back(fd);
    }
  }

  return make_tuple(set_read_fds, set_write_fds, set_error_fds);
}



} // namespace pixel_tools

