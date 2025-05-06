# Cython function 定義中的 `except` 關鍵字

* 不曉得實際原因。

```sh
python setup.py build_ext --inplace
python3 python_exception_in_cdef.py

# func_no_except_py
# [exception] func_no_except
# func_minus1_py
# [exception] func_minus1
# func_star_py
# [exception] func_star
# func_nogil_py
# [exception] func_nogil
```