cc_library(
  name = "pixel-server-lib",
  srcs = glob(["src/cpp_server/src/**/*.cpp"], exclude = ["src/ccp_server/src/main.cpp"]),
  hdrs = glob(["src/cpp_server/include/**/*.h"]),
  strip_include_prefix = "src/cpp_server/include/",
  linkopts = [
    "-pthread",
  ],
  deps = [
    "@rpi_ws281x//:rpi_ws281x",
    "@fmt//:fmt",
  ],
)

cc_binary(
  name = "pixel-server",
  srcs = ["src/cpp_server/src/main.cpp"],
  deps = [":pixel-server-lib"],
)
