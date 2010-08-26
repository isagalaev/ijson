=====
ijson
=====

Ijson is a Python wrapper to `YAJL <http://lloyd.github.com/yajl/>`_ which is a
streaming SAX-like JSON parser. Ijson provides a standard Python iterator
interface for it.

Usage
=====

Basic usage::

    from ijson import parse

    f = urlopen('http://.../') # some huge JSON
    parser = parse(f)
    while True:
        event, value = parser.next()
        if event == 'start_map':
            while event != 'end_map':
                event, value = parser.next()
                if event == 'map_key' and value == 'title':
                    event, value = parser.next()
                    do_something_with(value)

Acknowledgements
================

Ijson was inspired by `yajl-py <http://pykler.github.com/yajl-py/>`_ wrapper by
Hatem Nassrat. Though ijson borrows almost nothing from the actual yajl-py code
it was used as an example of integration with yajl using ctypes.
