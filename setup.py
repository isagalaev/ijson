# -*- coding:utf-8 -*-
from distutils.core import setup

setup(
    name = 'ijson',
    version = '0.8.0',
    author = 'Ivan Sagalaev',
    author_email = 'Maniac@SoftwareManiacs.Org',
    packages = ['ijson', 'ijson.backends'],
    url = 'https://github.com/isagalaev/ijson',
    license = 'LICENSE.txt',
    description = 'Iterative JSON parser with a standard Python iterator interface',
    long_description = open('README.rst').read(),
)
