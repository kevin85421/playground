cdef int func_no_except():
    raise ValueError("[exception] func_no_except")

cdef int func_minus1() except -1:
    raise ValueError("[exception] func_minus1")

cdef void func_star() except *:
    raise ValueError("[exception] func_star")

cdef void func_nogil() nogil:
    raise ValueError("[exception] func_nogil")

def func_no_except_py():
    return func_no_except()

def func_minus1_py():
    return func_minus1()

def func_star_py():
    return func_star()

def func_nogil_py():
    return func_nogil()
