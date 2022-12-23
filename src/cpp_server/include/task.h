/**
 * @brief Task class for managing a pthread
 */

#include <pthread.h>

#include "task_delegate.h"

#pragma once

namespace pixel_tools {


class Task {
public:
  Task(){};
  ~Task();

  Task(const Task& task) = delete;
  Task& operator=(const Task& task) = delete;

  void start();
  void stop();

  void set_delegate(TaskDelegate* delegate) {
    _delegate = delegate;
  }

  void ping();

  int ping_fd() {
    return _ping_pipe[0];
  }

private:
  pthread_t _thread;
  int _ping_pipe[2] = {-1};
  bool _shutdown = false;
  bool _running = false;
  TaskDelegate* _delegate = NULL;

  friend void* task_shim(void* arg);

  void loop();
};


} // namespace pixel_tools
