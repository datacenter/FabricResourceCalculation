from distutils.core import setup, Extension
setup(name='external_c_functions', version='1.0', ext_modules=[Extension('external_c_functions', ['external_c_functions.c'])])