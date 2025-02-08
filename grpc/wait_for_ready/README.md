# Wait for Ready

* 使用 bazel 編譯 grpc v1.66.0: https://github.com/grpc/grpc/blob/master/BUILDING.md#build-from-source
* 取代 [examples/cpp/helloworld](https://github.com/grpc/grpc/tree/v1.66.0/examples/cpp/helloworld) 中的 `greeter_server.cc` 和 `greeter_client.cc`

```sh
# 編譯
bazel build //examples/cpp/helloworld:greeter_server
bazel build //examples/cpp/helloworld:greeter_client

# 啟動 server，server 會 sleep 10 秒才開始 listen
bazel run //examples/cpp/helloworld:greeter_server
# or $GRPC_ROOT/bazel-bin/examples/cpp/helloworld/greeter_server

# 啟動 client，因為有設定 wait_for_ready，RPC 不會立刻 fail，而是會等待 server 開始 listen。
bazel run //examples/cpp/helloworld:greeter_client
# or $GRPC_ROOT/bazel-bin/examples/cpp/helloworld/greeter_client
```

