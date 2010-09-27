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
    '''
    Helper function casting a string that represents any Javascript number
    into appropriate Python value: either int or Decimal.
    '''
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
    # "integer" and "double" aren't actually yielded by yajl since "number"
    # takes precedence if defined
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

def basic_parse(f, allow_comments=False, check_utf8=False, buf_size=64 * 1024):
    '''
    An iterator returning events from a JSON being parsed. This basic parser
    doesn't maintain any context and just returns parser events from an
    underlying library, converting them into Python native data types.

    Parameters:

    - f: a readable file-like object with JSON input
    - allow_comments: tells parser to allow comments in JSON input
    - check_utf8: if True, parser will cause an error if input is invalid utf-8
    - buf_size: a size of an input buffer

    Events returned from parser are pairs of (event type, value) and can be as
    follows:

        ('null', None)
        ('boolean', <True or False>)
        ('number', <int or Decimal>)
        ('string', <unicode>)
        ('map_key', <str>)
        ('start_map', None)
        ('end_map', None)
        ('start_array', None)
        ('end_array', None)
    '''
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
        result = None
        buffer = f.read(buf_size)
        while buffer or result == YAJL_INSUFFICIENT_DATA:
            if buffer:
                result = yajl.yajl_parse(handle, buffer, len(buffer))
            else:
                result = yajl.yajl_parse_complete(handle)
            if result == YAJL_ERROR:
                error = yajl.yajl_get_error(handle, 1, buffer, len(buffer))
                raise JSONError(error)
            if events:
                for event in events:
                    yield event
                events = []
            buffer = f.read(buf_size)
    finally:
        yajl.yajl_free(handle)

def parse(*args, **kwargs):
    '''
    An iterator returning events from a JSON being parsed. This iterator
    provides the context of parser events accompanying them with a "prefix"
    value that contains the path to the nested elements from the root of the
    JSON document.

    For example, given this document:

        {
            "array": [1, 2],
            "map": {
                "key": "value"
            }
        }

    the parser would yield events:

        ('', 'start_map', None)
        ('', 'map_key', 'array')
        ('array', 'start_array', None)
        ('array.item', 'number', 1)
        ('array.item', 'number', 2)
        ('array', 'end_array', None)
        ('', 'map_key', 'map')
        ('map', 'start_map', None)
        ('map', 'map_key', 'key')
        ('map.key', 'string', u'value')
        ('map', 'end_map', None)
        ('', 'end_map', None)

    For the list of all available event types refer to `basic_parse` function.

    Parameters:

    - f: a readable file-like object with JSON input
    - allow_comments: tells parser to allow comments in JSON input
    - check_utf8: if True, parser will cause an error if input is invalid utf-8
    - buf_size: a size of an input buffer
    '''
    path = []
    for event, value in basic_parse(*args, **kwargs):
        if event == 'map_key':
            prefix = '.'.join(path[:-1])
            path[-1] = value
        elif event == 'start_map':
            prefix = '.'.join(path)
            path.append(None)
        elif event == 'end_map':
            path.pop()
            prefix = '.'.join(path)
        elif event == 'start_array':
            prefix = '.'.join(path)
            path.append('item')
        elif event == 'end_array':
            path.pop()
            prefix = '.'.join(path)
        else: # any scalar value
            prefix = '.'.join(path)

        yield prefix, event, value


class ObjectBuilder(object):
    '''
    Incrementally builds an object from JSON parser events. Events are passed
    into the `event` function that accepts two parameters: event type and
    value. The object being built is available at any time from the `value`
    attribute.

    Example:

        from StringIO import StringIO
        from ijson.parse import basic_parse
        from ijson.utils import ObjectBuilder

        builder = ObjectBuilder()
        f = StringIO('{"key": "value"})
        for event, value in basic_parse(f):
            builder.event(event, value)
        print builder.value

    '''
    def __init__(self):
        def initial_set(value):
            self.value = value
        self.containers = [initial_set]

    def event(self, event, value):
        if event == 'map_key':
            self.key = value
        elif event == 'start_map':
            map = {}
            self.containers[-1](map)
            def setter(value):
                map[self.key] = value
            self.containers.append(setter)
        elif event == 'start_array':
            array = []
            self.containers[-1](array)
            self.containers.append(array.append)
        elif event == 'end_array' or event == 'end_map':
            self.containers.pop()
        else:
            self.containers[-1](value)

def items(file, prefix):
    '''
    Iterates over a file objects and everything found under given prefix as
    as native Python objects.
    '''
    parser = iter(parse(file))
    try:
        while True:
            current, event, value = parser.next()
            if current == prefix:
                builder = ObjectBuilder()
                if event in ('start_map', 'start_array'):
                    end_event = event.replace('start', 'end')
                    while (current, event) != (prefix, end_event):
                        builder.event(event, value)
                        current, event, value = parser.next()
                else:
                    builder.event(event, value)
                yield builder.value
    except StopIteration:
        pass
