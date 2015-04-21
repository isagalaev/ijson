

class YAJLImportError(ImportError):
    pass


def find_yajl(required):
    '''
    Finds and loads yajl shared object of the required major
    version (1, 2, ...).
    '''
    # Importing ``ctypes`` should be in scope of this function to prevent failure
    # of `backends`` package load in a runtime where ``ctypes`` is not available.
    # Example of such environment is Google App Engine (GAE).
    from ctypes import util, cdll

    so_name = util.find_library('yajl')
    if so_name is None:
        raise YAJLImportError('YAJL shared object not found.')
    yajl = cdll.LoadLibrary(so_name)
    major, rest = divmod(yajl.yajl_version(), 10000)
    minor, micro = divmod(rest, 100)
    if major != required:
        raise YAJLImportError('YAJL version %s.x required, found %s.%s.%s' % (required, major, minor, micro))
    return yajl
