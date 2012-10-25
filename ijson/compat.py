'''
Python2/Python3 compatibility utilities.
'''

import sys


IS_PY2 = sys.version_info[0] < 3


if IS_PY2:
    def u(s):
        return s.decode('utf-8')
    b = lambda s: s
    s = b
    b2s = b
else:
    u = lambda s: s
    def b(s):
        return s.encode('utf-8')
    s = u
    def b2s(b):
        return b.decode('utf-8')
