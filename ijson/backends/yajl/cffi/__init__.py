from ijson.backends import YAJLImportError


def require_version(version, required):
    major, rest = divmod(version, 10000)
    minor, micro = divmod(rest, 100)
    if major != required:
        raise YAJLImportError('YAJL version %s.x required, found %s.%s.%s' % (required, major, minor, micro))
