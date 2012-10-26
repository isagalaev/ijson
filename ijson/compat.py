'''
Python2/Python3 compatibility utilities.
'''

import sys


IS_PY2 = sys.version_info[0] < 3


if IS_PY2:
    b2s = lambda s: s
else:
    def b2s(b):
        return b.decode('utf-8')
