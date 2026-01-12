# BPE Tokenizer Training

* See [section 2.5](https://github.com/kevin85421/assignment1-basics/blob/main/cs336_spring2025_assignment1_basics.pdf)
* Code: https://github.com/kevin85421/assignment1-basics/blob/main/cs336_basics/train_bpe.py
* Test
    ```sh
    uv run pytest -vvs tests/test_train_bpe.py

    ...
    tests/test_train_bpe.py::test_train_bpe_speed PASSED
    tests/test_train_bpe.py::test_train_bpe PASSED
    tests/test_train_bpe.py::test_train_bpe_special_tokens PASSED
    ```