from ctypes import cdll, util

name = util.find_library('yajl')
if name is None:
    raise Exception('YAJL shared object not found.')
yajl = cdll.LoadLibrary(name)
