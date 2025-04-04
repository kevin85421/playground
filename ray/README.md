# Bazel 編譯時避免 CPU overloading

* Solution 1:
    ```sh
    bazel build -c fastbuild //:ray_pkg --jobs=16
    ```

* Solution 2:
    ```sh
    # 設定 .bazelrc
    build --jobs=16

    # compile
    pip install -e . --verbose
    ```