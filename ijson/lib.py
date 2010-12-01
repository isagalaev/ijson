from ctypes import cdll, util, c_char, POINTER

name = util.find_library('yajl')
if name is None:
    raise Exception('YAJL shared object not found.')
yajl = cdll.LoadLibrary(name)

yajl.yajl_alloc.restype = POINTER(c_char)
yajl.yajl_gen_alloc.restype = POINTER(c_char)
yajl.yajl_gen_alloc2.restype = POINTER(c_char)
