"""
Setup script to compile the Cython SVD model

to compile: python setup.py build_ext --inplace
"""
from setuptools import setup
from Cython.Build import cythonize
import numpy as np
setup(
    ext_modules=cythonize("svd.pyx"),
    include_dirs=[np.get_include()]
)