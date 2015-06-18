try:
    from ijson.backends.yajl.cffi import yajl2 as _yajl
except ImportError:
    try:
        from ijson.backends.yajl.ctypes import yajl2 as _yajl
    except ImportError:
        try:
            from ijson.backends.yajl.cffi import yajl as _yajl
        except ImportError:
            from ijson.backends.yajl.ctypes import yajl as _yajl


basic_parse = _yajl.basic_parse
parse = _yajl.parse
items = _yajl.items
