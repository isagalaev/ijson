'''
Python2/Python3 compatibility utilities.
'''

import sys


IS_PY2 = sys.version_info[0] < 3


if IS_PY2:
    b2s = lambda s: s
    def s2u(s):
        return s.decode('utf-8')
    chr = unichr
else:
    def b2s(b):
        return b.decode('utf-8')
    s2u = lambda s: s
    chr = chr
