from ijson.common import JSONError, IncompleteJSONError, ObjectBuilder
from ijson.backends import WrongVersion

try:
    import ijson.backends.yajl2 as backend
except WrongVersion:
    try:
        import ijson.backends.yajl as backend
    except WrongVersion:
        import ijson.backends.python as backend


basic_parse = backend.basic_parse
parse = backend.parse
items = backend.items
