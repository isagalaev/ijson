'''
Wrapper for YAJL C library version 1.x.
'''

from ctypes import Structure, c_uint, c_ubyte, c_int, c_long, c_double, c_char, \
                   c_void_p, c_char_p, CFUNCTYPE, POINTER, byref, string_at, cast
import sys

from ijson import common
from ijson.compat import b2s
from ijson.backends.yajl.ctypes import find_yajl
import ijson.backends.yajl.common


yajl = find_yajl(1)
yajl.yajl_alloc.restype = POINTER(c_char)
yajl.yajl_get_error.restype = POINTER(c_char)

C_EMPTY = CFUNCTYPE(c_int, c_void_p)
C_INT = CFUNCTYPE(c_int, c_void_p, c_int)
C_LONG = CFUNCTYPE(c_int, c_void_p, c_long)
C_DOUBLE = CFUNCTYPE(c_int, c_void_p, c_double)
C_STR = CFUNCTYPE(c_int, c_void_p, POINTER(c_ubyte), c_uint)


_callback_data = [
    # Mapping of JSON parser events to callback C types and value converters.
    # Used to define the Callbacks structure and actual callback functions
    # inside the parse function.
    ('null', C_EMPTY, lambda: None),
    ('boolean', C_INT, lambda v: bool(v)),
    # "integer" and "double" aren't actually yielded by yajl since "number"
    # takes precedence if defined
    ('integer', C_LONG, lambda v, l: int(string_at(v, l))),
    ('double', C_DOUBLE, lambda v, l: float(string_at(v, l))),
    ('number', C_STR, lambda v, l: common.number(b2s(string_at(v, l)))),
    ('string', C_STR, lambda v, l: string_at(v, l).decode('utf-8')),
    ('start_map', C_EMPTY, lambda: None),
    ('map_key', C_STR, lambda v, l: b2s(string_at(v, l))),
    ('end_map', C_EMPTY, lambda: None),
    ('start_array', C_EMPTY, lambda: None),
    ('end_array', C_EMPTY, lambda: None),
]

class Callbacks(Structure):
    _fields_ = [(name, type) for name, type, func in _callback_data]

class Config(Structure):
    _fields_ = [
        ("allowComments", c_uint),
        ("checkUTF8", c_uint)
    ]

YAJL_OK = 0
YAJL_CANCELLED = 1
YAJL_INSUFFICIENT_DATA = 2
YAJL_ERROR = 3


def yajl_init(scope, events, allow_comments=False, check_utf8=False):
    def callback(event, func_type, func):
        def c_callback(context, *args):
            events.append((event, func(*args)))
            return 1
        return func_type(c_callback)

    scope.callbacks = Callbacks(*[callback(*data) for data in _callback_data])
    config = Config(allow_comments, check_utf8)

    handle = yajl.yajl_alloc(byref(scope.callbacks), byref(config), None, None)
    return handle

def yajl_parse(handle, buffer):
    if buffer:
        result = yajl.yajl_parse(handle, buffer, len(buffer))
    else:
        result = yajl.yajl_parse_complete(handle)

    if result != YAJL_OK:
        perror = yajl.yajl_get_error(handle, 1, buffer, len(buffer))
        error = cast(perror, c_char_p).value
        yajl.yajl_free_error(handle, perror)
        exception = common.IncompleteJSONError if result == YAJL_INSUFFICIENT_DATA else common.JSONError
        raise exception(error)


def yajl_free(handle):
    yajl.yajl_free(handle)


def basic_parse(f, buf_size=64*1024, allow_comments=False, check_utf8=False):
    _yajl = sys.modules[__name__]
    return ijson.backends.yajl.common.basic_parse(
        _yajl, f, buf_size=buf_size,
        allow_comments=allow_comments, check_utf8=check_utf8
    )

def parse(file, **kwargs):
    _yajl = sys.modules[__name__]
    return ijson.backends.yajl.common.parse(_yajl, file, **kwargs)


def items(file, prefix):
    _yajl = sys.modules[__name__]
    return ijson.backends.yajl.common.items(_yajl, file, prefix)

