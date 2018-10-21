# Always prefer setuptools over distutils
from os import path
from codecs import open  # To use a consistent encoding
from setuptools import setup
from Cython.Build import cythonize
import numpy

# Get the long description from the relevant file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='misu',
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version='1.0.6',
    description='Fast quantities',
    long_description=long_description,
    url='https://github.com/cjrh/misu',
    author='Caleb Hattingh',
    author_email='caleb.hattingh@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='math science engineering physics quantities units',
    packages=['misu'],
    install_requires=['cython', 'numpy'],
    ext_modules=cythonize("misu/*.pyx"),
    include_dirs=[numpy.get_include()]
)
