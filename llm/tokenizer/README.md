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

# BPE tokenizer

* See [section 2.6](https://github.com/kevin85421/assignment1-basics/blob/main/cs336_spring2025_assignment1_basics.pdf)
* Code: https://github.com/kevin85421/assignment1-basics/blob/main/cs336_basics/tokenizer.py
* Test
    ```sh
    uv run pytest -vvs tests/test_tokenizer.py 2>&1 | tee log

    ...
    tests/test_tokenizer.py::test_roundtrip_empty PASSED
    tests/test_tokenizer.py::test_empty_matches_tiktoken PASSED
    tests/test_tokenizer.py::test_roundtrip_single_character PASSED
    tests/test_tokenizer.py::test_single_character_matches_tiktoken PASSED
    tests/test_tokenizer.py::test_roundtrip_single_unicode_character PASSED
    tests/test_tokenizer.py::test_single_unicode_character_matches_tiktoken PASSED
    tests/test_tokenizer.py::test_roundtrip_ascii_string PASSED
    tests/test_tokenizer.py::test_ascii_string_matches_tiktoken PASSED
    tests/test_tokenizer.py::test_roundtrip_unicode_string PASSED
    tests/test_tokenizer.py::test_unicode_string_matches_tiktoken PASSED
    tests/test_tokenizer.py::test_roundtrip_unicode_string_with_special_tokens PASSED
    tests/test_tokenizer.py::test_unicode_string_with_special_tokens_matches_tiktoken PASSED
    tests/test_tokenizer.py::test_overlapping_special_tokens PASSED
    tests/test_tokenizer.py::test_address_roundtrip PASSED
    tests/test_tokenizer.py::test_address_matches_tiktoken PASSED
    tests/test_tokenizer.py::test_german_roundtrip PASSED
    tests/test_tokenizer.py::test_german_matches_tiktoken PASSED
    tests/test_tokenizer.py::test_tinystories_sample_roundtrip PASSED
    tests/test_tokenizer.py::test_tinystories_matches_tiktoken PASSED
    tests/test_tokenizer.py::test_encode_special_token_trailing_newlines PASSED
    tests/test_tokenizer.py::test_encode_special_token_double_newline_non_whitespace PASSED
    tests/test_tokenizer.py::test_encode_iterable_tinystories_sample_roundtrip PASSED
    tests/test_tokenizer.py::test_encode_iterable_tinystories_matches_tiktoken PASSED
    tests/test_tokenizer.py::test_encode_iterable_memory_usage PASSED
    tests/test_tokenizer.py::test_encode_memory_usage XFAILallotted (1MB).)
    ```
