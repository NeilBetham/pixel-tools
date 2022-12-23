filegroup(
  name = "rpi_ws281x_hdrs",
  srcs = glob(["*.h"]),
)

filegroup(
  name = "rpi_ws281x_srcs",
  srcs = glob(["*.c"], exclude = ["main.c"]),
)


cc_library(
  name = "rpi_ws281x",
  srcs = [":rpi_ws281x_srcs"],
  hdrs = [":rpi_ws281x_hdrs"],
  linkstatic = True,
  linkopts = ["-lm"],
  visibility = ["//visibility:public"],
)
