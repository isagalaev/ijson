'''
Iterative JSON parser.

Main API:

- ``ijson.parse``: iterator returning parsing events with the object tree context,
  see ``ijson.common.parse`` for docs.

- ``ijson.items``: iterator returning Python objects found under a specified prefix,
  see ``ijson.common.items`` for docs.

Top-level ``ijson`` module tries to automatically find and import a suitable
parsing backend. You can also explicitly import a required backend from
``ijson.backends``.
'''

from ijson.common import JSONError, IncompleteJSONError, ObjectBuilder
from ijson.backends import YAJLImportError

try:
    import ijson.backends.yajl2 as backend
except YAJLImportError:
    try:
        import ijson.backends.yajl as backend
    except YAJLImportError:
        import ijson.backends.python as backend


basic_parse = backend.basic_parse
parse = backend.parse
items = backend.items
