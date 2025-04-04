# Bazel 編譯時避免 CPU overloading

```sh
bazel build -c fastbuild //:ray_pkg --jobs=16
```