from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "cython_utils",
        ["cython_utils.pyx"],
    )
]

setup(
    name="cython_utils",
    ext_modules=cythonize(extensions),
)
