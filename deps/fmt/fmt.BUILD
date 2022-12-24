filegroup(
  name = "fmt_headers",
  srcs = glob(["include/**/*.h"]),
)

cc_library(
  name = "fmt",
  hdrs = [":fmt_headers"],
  strip_include_prefix = "include",
  visibility = ["//visibility:public"],
)
