from ctypes import Structure, c_uint, c_ubyte, c_int, c_long, c_double, \
                   c_void_p, c_char_p, CFUNCTYPE, POINTER, byref, string_at
from decimal import Decimal

from ijson.lib import yajl

C_EMPTY = CFUNCTYPE(c_int, c_void_p)
C_INT = CFUNCTYPE(c_int, c_void_p, c_int)
C_LONG = CFUNCTYPE(c_int, c_void_p, c_long)
C_DOUBLE = CFUNCTYPE(c_int, c_void_p, c_double)
C_STR = CFUNCTYPE(c_int, c_void_p, POINTER(c_ubyte), c_uint)

def number(value):
    try:
        return int(value)
    except ValueError:
        return Decimal(value)

_callback_data = [
    # Mapping of JSON parser events to callback C types and value converters.
    # Used to define the Callbacks structure and actual callback functions
    # inside the parse function.
    ('null', C_EMPTY, lambda: None),
    ('boolean', C_INT, lambda v: bool(v)),
    ('integer', C_LONG, lambda v, l: int(string_at(v, l))),
    ('double', C_DOUBLE, lambda v, l: float(string_at(v, l))),
    ('number', C_STR, lambda v, l: number(string_at(v, l))),
    ('string', C_STR, lambda v, l: string_at(v, l).decode('utf-8')),
    ('start_map', C_EMPTY, lambda: None),
    ('map_key', C_STR, lambda v, l: string_at(v, l)),
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

class JSONError(Exception):
    pass

class ParseCancelledError(JSONError):
    def __init__(self):
        super(ParseCancelledError, self).__init__('Parsing cancelled by a callback')

def parse(f, allow_comments=False, check_utf8=False, buf_size=64 * 1024):
    events = []

    def callback(event, func_type, func):
        def c_callback(context, *args):
            events.append((event, func(*args)))
            return 1
        return func_type(c_callback)

    yajl.yajl_get_error.restype = c_char_p
    callbacks = Callbacks(*[callback(*data) for data in _callback_data])
    config = Config(allow_comments, check_utf8)
    handle = yajl.yajl_alloc(byref(callbacks), byref(config), None, None)
    try:
        while True:
            buffer = f.read(buf_size)
            if buffer:
                result = yajl.yajl_parse(handle, buffer, len(buffer))
            else:
                result = yajl.yajl_parse_complete(handle)
            if not buffer or (result in (YAJL_CANCELLED, YAJL_ERROR)):
                break
            for event, value in events:
                yield event, value
            events = []

        if result == YAJL_CANCELLED:
            raise ParseCancelledError()
        elif result == YAJL_ERROR:
            error = yajl.yajl_get_error(handle, 1, buffer, len(buffer))
            raise JSONError(error)
    finally:
        yajl.yajl_free(handle)
