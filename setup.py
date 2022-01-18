from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules = cythonize('preprocessing.pyx'))
setup(ext_modules = cythonize('Model.pyx'))
setup(ext_modules = cythonize('Network.pyx'))
setup(ext_modules = cythonize('vaccination.pyx'))
setup(ext_modules = cythonize('Parameters.pyx'))
setup(ext_modules = cythonize('Run.pyx'))
setup(ext_modules = cythonize('initialize.pyx'))
setup(ext_modules = cythonize('Read_data.pyx'))

