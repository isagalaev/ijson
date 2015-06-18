from ijson import common


class Container(object):
    pass


def basic_parse(yajl, f, buf_size=64*1024, **config):
    '''
    Iterator yielding unprefixed events.

    Parameters:

    - f: a readable file-like object with JSON input
    - allow_comments: tells parser to allow comments in JSON input
    - buf_size: a size of an input buffer
    - multiple_values: allows the parser to parse multiple JSON objects
    '''

    # the scope objects makes sure the C objects allocated in _yajl.init
    # are kept alive until this function is done
    scope = Container()
    events = []

    handle = yajl.yajl_init(scope, events, **config)
    try:
        while True:
            buffer = f.read(buf_size)
            # this calls the callbacks which will
            # fill the events list
            yajl.yajl_parse(handle, buffer)

            if not buffer and not events:
                break

            for event in events:
                yield event

            # clear all events, but don't replace the
            # the events list instance
            del events[:]
    finally:
        yajl.yajl_free(handle)


def parse(yajl, file, **kwargs):
    '''
    Backend-specific wrapper for ijson.common.parse.
    '''
    return common.parse(basic_parse(yajl, file, **kwargs))

def items(yajl, file, prefix):
    '''
    Backend-specific wrapper for ijson.common.items.
    '''
    return common.items(parse(yajl, file), prefix)
