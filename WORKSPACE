workspace(name = "pixel-tools")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
  name = "rpi_ws281x",
  url = "https://github.com/jgarff/rpi_ws281x/archive/1ba8e385708fb7802b09c0177a7ea4293948e25c.tar.gz",
  sha256 = "027fd7749654b7e0760cde0f0a816c297ffdf781e0b51ae0567db2a47f6f7f88",
  strip_prefix = "rpi_ws281x-1ba8e385708fb7802b09c0177a7ea4293948e25c",
  build_file = "@//deps/rpi_ws281x:rpi_ws281x.BUILD"
)
