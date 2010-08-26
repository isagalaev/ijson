# -*- coding:utf-8 -*-
from distutils.core import setup

setup(
    name = 'ijson',
    version = '0.1.0',
    author = 'Ivan Sagalaev',
    author_email = 'Maniac@SoftwareManiacs.Org',
    packages = ['ijson'],
    url = 'https://launchpad.net/ijson',
    license = 'LICENSE.txt',
    description = 'A Python wrapper to YAJL providing standard iterator interface to streaming JSON parsing',
    long_description = open('README.txt').read(),
)
