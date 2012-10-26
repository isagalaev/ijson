# -*- coding:utf-8 -*-
from distutils.core import setup

setup(
    name = 'ijson',
    version = '1.0',
    author = 'Ivan Sagalaev',
    author_email = 'maniac@softwaremaniacs.org',
    packages = ['ijson', 'ijson.backends'],
    url = 'https://github.com/isagalaev/ijson',
    license = open('LICENSE.txt').read(),
    description = 'Iterative JSON parser with a standard Python iterator interface',
    long_description = open('README.rst').read(),
)
