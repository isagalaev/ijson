class JSONError(Exception):
    pass

class IncompleteJSONError(JSONError):
    def __init__(self):
        super(IncompleteJSONError, self).__init__('Incomplete or empty JSON data')

def parse(basic_events):
    '''
    An iterator returning prefixed events from the basic events as returned from
    a backend's `basic_parse`. Prefixes represent the path to the nested elements
    from the root of the JSON document.

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
    for event, value in basic_events:
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

def items(prefixed_events, prefix):
    '''
    An iterator returning native Python objects constructed from the events
    under a given prefix. The `prefixed_events` is an iterator of events as
    returned from `parse`.
    '''
    prefixed_events = iter(prefixed_events)
    try:
        while True:
            current, event, value = prefixed_events.next()
            if current == prefix:
                if event in ('start_map', 'start_array'):
                    builder = ObjectBuilder()
                    end_event = event.replace('start', 'end')
                    while (current, event) != (prefix, end_event):
                        builder.event(event, value)
                        current, event, value = prefixed_events.next()
                    yield builder.value
                else:
                    yield value
    except StopIteration:
        pass
