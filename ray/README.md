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

# Ray task/PG fault tolerance

```sh
ray start --head --num-cpus=0
ray start --address=127.0.0.1:6379

# https://gist.github.com/kevin85421/5d5e1c25f3546dcd9093778836473094
# schedule a PG on the worker node, and then schedule a long running task to the PG.
python3 pg_task_retry.py

# Get PID of the worker's Raylet
ps aux | grep "raylet.1"
kill $WORKER_RAYLET_PID

# List tasks
ray list tasks

# ======== List: 2025-09-05 06:46:40.758510 ========
# Stats:
# ------------------------------
# Total: 3
#
# Table:
# ------------------------------
#     TASK_ID                                             ATTEMPT_NUMBER  NAME                           STATE                      JOB_ID  ACTOR_ID    TYPE         FUNC_OR_CLASS_NAME             PARENT_TASK_ID                                    NODE_ID                                                   WORKER_ID                           #                         WORKER_PID  ERROR_TYPE
#  0  16310a0f0a45af5cffffffffffffffffffffffff01000000                 1  sleep                          PENDING_NODE_ASSIGNMENT  01000000              NORMAL_TASK  sleep                          ffffffffffffffffffffffffffffffffffffffff01000000
#  1  16310a0f0a45af5cffffffffffffffffffffffff01000000                 0  sleep                          FAILED                   01000000              NORMAL_TASK  sleep                          ffffffffffffffffffffffffffffffffffffffff01000000  03dcce5b881f347f2501a0b064d018dd84f4fe656d31535ee296eee6  0f5288126e9974bbfa8c716ba44ed6f9326f754f1db2760cec7bd0ce         84491  NODE_DIED
#  2  c8ef45ccd0112571ffffffffffffffffffffffff01000000                 0  bundle_reservation_check_func  FINISHED                 01000000              NORMAL_TASK  bundle_reservation_check_func  ffffffffffffffffffffffffffffffffffffffff01000000  03dcce5b881f347f2501a0b064d018dd84f4fe656d31535ee296eee6  0f5288126e9974bbfa8c716ba44ed6f9326f754f1db2760cec7bd0ce         84491

# start a new worker node
ray start --address=127.0.0.1:6379

# List tasks
ray list tasks

# ======== List: 2025-09-05 06:47:13.113043 ========
# Stats:
# ------------------------------
# Total: 3
#
# Table:
# ------------------------------
#     TASK_ID                                             ATTEMPT_NUMBER  NAME                           STATE       JOB_ID  ACTOR_ID    TYPE         FUNC_OR_CLASS_NAME             PARENT_TASK_ID                                    NODE_ID                                                   WORKER_ID                                                   WORKER_PID  ERROR_TYPE
#  0  16310a0f0a45af5cffffffffffffffffffffffff01000000                 1  sleep                          RUNNING   01000000              NORMAL_TASK  sleep                          ffffffffffffffffffffffffffffffffffffffff01000000  1d4e75537ec3484e20222dd4ed68e3160e3429df9fd9a713fa1418e5  662657a759ef0caa9ee0359e59288ee7427237ecbec9942f9c2c5762         85184
#  1  16310a0f0a45af5cffffffffffffffffffffffff01000000                 0  sleep                          FAILED    01000000              NORMAL_TASK  sleep                          ffffffffffffffffffffffffffffffffffffffff01000000  03dcce5b881f347f2501a0b064d018dd84f4fe656d31535ee296eee6  0f5288126e9974bbfa8c716ba44ed6f9326f754f1db2760cec7bd0ce         84491  NODE_DIED
#  2  c8ef45ccd0112571ffffffffffffffffffffffff01000000                 0  bundle_reservation_check_func  FINISHED  01000000              NORMAL_TASK  bundle_reservation_check_func  ffffffffffffffffffffffffffffffffffffffff01000000  03dcce5b881f347f2501a0b064d018dd84f4fe656d31535ee296eee6  0f5288126e9974bbfa8c716ba44ed6f9326f754f1db2760cec7bd0ce         84491

```
