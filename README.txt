=====
ijson
=====

Ijson is a Python wrapper to `YAJL <http://lloyd.github.com/yajl/>`_ which is a
streaming SAX-like JSON parser. Ijson provides a standard Python iterator
interface for it.

Usage
=====

Common usage::

    from ijson import parse

    f = urlopen('http://.../') # some huge JSON
    parser = parse(f)
    while True:
        prefix, event, value = parser.next()
        if prefix == 'earth.europe' and event == 'start_array':
            while prefix.startswith('earth.europe'):
                prefix, event, value = parser.next()
                if event == 'map_key':
                    key = value
                    prefix, event, value = parser.next()
                    do_something_with(key, value)

Acknowledgements
================

Ijson was inspired by `yajl-py <http://pykler.github.com/yajl-py/>`_ wrapper by
Hatem Nassrat. Though ijson borrows almost nothing from the actual yajl-py code
it was used as an example of integration with yajl using ctypes.
