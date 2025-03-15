load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Add bazel_skylib
http_archive(
    name = "bazel_skylib",
    urls = ["https://github.com/bazelbuild/bazel-skylib/releases/download/1.4.2/bazel-skylib-1.4.2.tar.gz"],
    sha256 = "66ffd9315665bfaafc96b52278f57c7e2dd09f5ede279ea6d39b2be471e7e3aa",
)

# Setup rules_boost
http_archive(
    name = "com_github_nelhage_rules_boost",
    urls = ["https://github.com/nelhage/rules_boost/archive/refs/heads/master.tar.gz"],
    strip_prefix = "rules_boost-master",
)

load("@com_github_nelhage_rules_boost//:boost/boost.bzl", "boost_deps")
boost_deps()
