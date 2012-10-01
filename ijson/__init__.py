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
