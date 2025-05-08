cc_binary(
    name = "thread_pool_wait_and_join",
    srcs = ["cpp/thread_pool_wait_and_join.cc"],
    deps = [
        "@boost//:asio",
        "@boost//:system",
    ],
) 

cc_binary(
    name = "thread_pool_stop",
    srcs = ["cpp/thread_pool_stop.cc"],
    deps = [
        "@boost//:asio",
    ],
)

cc_binary(
    name = "flat_hash_map_with_normal_ptr",
    srcs = ["cpp/flat_hash_map_with_normal_ptr.cc"],
    deps = [
        "@absl//absl/container:flat_hash_map",
    ],
)

cc_binary(
    name = "flat_hash_map_with_smart_ptr",
    srcs = ["cpp/flat_hash_map_with_smart_ptr.cc"],
    deps = [
        "@absl//absl/container:flat_hash_map",
    ],
)

cc_binary(
    name = "boost_latch",
    srcs = ["cpp/boost_latch.cc"],
    deps = [
        "@boost//:thread",
    ],
)