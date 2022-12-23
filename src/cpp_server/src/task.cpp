#include "task.h"

#include <stdint.h>
#include <string.h>
#include <unistd.h>

namespace pixel_tools {

void* task_shim(void* arg) {
  Task* task = (Task*)arg;
  task->loop();
  return NULL;
}


Task::~Task() {
  stop();
}

void Task::start() {
  _shutdown = false;
  if(!_running) {
    memset(&_thread, 0, sizeof(_thread));
    pthread_create(&_thread, NULL, task_shim, this);
  }
}

void Task::stop() {
  _shutdown = true;
  if(_running) {
    ping();
    pthread_join(_thread, NULL);
  }
}

void Task::ping() {
  uint8_t buf = 0;
  write(_ping_pipe[1], &buf, 1);
}

void Task::loop() {
  _running = true;
  while(!_shutdown) {
    if(_delegate) {
      _delegate->loop();
    }
  }
  _running = false;
}


} // namespace pixel_tools
