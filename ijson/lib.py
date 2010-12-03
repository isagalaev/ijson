from ctypes import cdll, util, c_char, POINTER

name = util.find_library('yajl')

# Temporary hack for Hardy 64. find_library doesn't find this file for some
# reason.
if name is None:
    import os
    hardy64_name = '/usr/lib/libyajl.so.1'
    os.path.exists(hardy64_name):
        name = hardy64_name

if name is None:
    raise Exception('YAJL shared object not found.')
yajl = cdll.LoadLibrary(name)

yajl.yajl_alloc.restype = POINTER(c_char)
yajl.yajl_gen_alloc.restype = POINTER(c_char)
yajl.yajl_gen_alloc2.restype = POINTER(c_char)
