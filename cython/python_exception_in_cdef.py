import cython_utils

print("func_no_except_py")
try:
    cython_utils.func_no_except_py()
except Exception as e:
    print(e)

print("func_minus1_py")
try:
    cython_utils.func_minus1_py()
except Exception as e:
    print(e)

print("func_star_py")
try:
    cython_utils.func_star_py()
except Exception as e:
    print(e)

# 預期不應該丟出 exception，但是實際上還是有。
print("func_nogil_py")
try:
    cython_utils.func_nogil_py()
except Exception as e:
    print(e)
