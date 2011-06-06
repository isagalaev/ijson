=====
ijson
=====

Ijson is a Python wrapper to `YAJL <http://lloyd.github.com/yajl/>`_ which is a
streaming SAX-like JSON parser. Ijson provides a standard Python iterator
interface for it.


Usage
=====

All usage example will be using a JSON document describing geographical
objects::

    {
      "earth": {
        "europe": [
          {"name": "Paris", "type": "city", "info": { ... }},
          {"name": "Thames", "type": "river", "info": { ... }},
          // ...
        ],
        "america": [
          {"name": "Texas", "type": "state", "info": { ... }},
          // ...
        ]
      }
    }

Most common usage is having ijson yield native Python objects out of a JSON
stream located under a prefix. Here's how to process all European cities::

    from ijson import items

    f = urlopen('http://.../')
    objects = items(f, 'earth.europe.item')
    cities = (o for o in objects if o['type'] == 'city')
    for city in cities:
        do_something_with(city)

Sometimes when dealing with a particularly large JSON payload it may worth to
not even construct individual Python objects and react on individual events
immediately producing some result::

    from ijson import parse

    f = urlopen('http://.../')
    parser = parse(f)
    stream.write('<geo>')
    for prefix, event, value in parser:
        if (prefix, event) == ('earth', 'map_key'):
            stream.write('<%s>' % value)
            continent = value
        elif prefix.endswith('.name'):
            stream.write('<object name="%s"/>' % value)
        elif (prefix, event) == ('earth.%s' % continent, 'end_map'):
            stream.write('</%s>' % continent)
    stream.write('</geo>')


Acknowledgements
================

Ijson was inspired by `yajl-py <http://pykler.github.com/yajl-py/>`_ wrapper by
Hatem Nassrat. Though ijson borrows almost nothing from the actual yajl-py code
it was used as an example of integration with yajl using ctypes.
