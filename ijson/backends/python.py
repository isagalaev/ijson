'''
Pure-python parsing backend.
'''

from decimal import Decimal
import re
from codecs import unicode_escape_decode

from ijson import common
from ijson.compat import s, b2s


BUFSIZE = 16 * 1024
NONWS = re.compile(r'\S')
LEXTERM = re.compile(r'[^a-z0-9\.-]')


class UnexpectedSymbol(common.JSONError):
    def __init__(self, symbol, reader):
        super(UnexpectedSymbol, self).__init__('Unexpected symbol "%s" at %d' % (symbol[0], reader.pos - len(symbol)))

class Lexer(object):
    '''
    JSON lexer. Supports iterator interface.
    '''
    def __init__(self, f):
        self.f = f

    def __iter__(self):
        self.buffer = s('')
        self.pos = 0
        return self

    def __next__(self):
        while True:
            match = NONWS.search(self.buffer, self.pos)
            if match:
                self.pos = match.start()
                char = self.buffer[self.pos]
                if 'a' <= char <= 'z' or '0' <= char <= '9' or char == '-':
                    return self.lexem()
                elif char == '"':
                    return self.stringlexem()
                else:
                    self.pos += 1
                    return char
            self.buffer = b2s(self.f.read(BUFSIZE))
            self.pos = 0
            if not len(self.buffer):
                raise common.IncompleteJSONError()
    next = __next__

    def lexem(self):
        current = self.pos
        while True:
            match = LEXTERM.search(self.buffer, current)
            if match:
                current = match.start()
                break
            else:
                current = len(self.buffer)
                self.buffer += b2s(self.f.read(BUFSIZE))
                if len(self.buffer) == current:
                    break
        result = self.buffer[self.pos:current]
        self.pos = current
        if self.pos > BUFSIZE:
            self.buffer = self.buffer[self.pos:]
            self.pos = 0
        return result

    def stringlexem(self):
        start = self.pos + 1
        while True:
            try:
                end = self.buffer.index('"', start)
                escpos = end - 1
                while self.buffer[escpos] == '\\':
                    escpos -= 1
                if (end - escpos) % 2 == 0:
                    start = end + 1
                else:
                    result = self.buffer[self.pos:end + 1]
                    self.pos = end + 1
                    return result
            except ValueError:
                old_len = len(self.buffer)
                self.buffer += b2s(self.f.read(BUFSIZE))
                if len(self.buffer) == old_len:
                    raise common.IncompleteJSONError()

def parse_value(lexer, symbol=None):
    if symbol == None:
        symbol = lexer.next()
    if symbol == 'null':
        yield ('null', None)
    elif symbol == 'true':
        yield ('boolean', True)
    elif symbol == 'false':
        yield ('boolean', False)
    elif symbol == '[':
        for event in parse_array(lexer):
            yield event
    elif symbol == '{':
        for event in parse_object(lexer):
            yield event
    elif symbol[0] == '"':
        yield ('string', unicode_escape_decode(symbol[1:-1])[0])
    else:
        try:
            number = Decimal(symbol) if '.' in symbol else int(symbol)
            yield ('number', number)
        except ValueError:
            raise UnexpectedSymbol(symbol, lexer)

def parse_array(lexer):
    yield ('start_array', None)
    symbol = lexer.next()
    if symbol != ']':
        while True:
            for event in parse_value(lexer, symbol):
                yield event
            symbol = lexer.next()
            if symbol == ']':
                break
            if symbol != ',':
                raise UnexpectedSymbol(symbol, lexer)
            symbol = lexer.next()
    yield ('end_array', None)

def parse_object(lexer):
    yield ('start_map', None)
    symbol = lexer.next()
    if symbol != '}':
        while True:
            if symbol[0] != '"':
                raise UnexpectedSymbol(symbol, lexer)
            yield ('map_key', symbol[1:-1])
            symbol = lexer.next()
            if symbol != ':':
                raise UnexpectedSymbol(symbol, lexer)
            for event in parse_value(lexer):
                yield event
            symbol = lexer.next()
            if symbol == '}':
                break
            if symbol != ',':
                raise UnexpectedSymbol(symbol, lexer)
            symbol = lexer.next()
    yield ('end_map', None)

def basic_parse(file):
    '''
    Iterator yielding unprefixed events.

    Parameters:

    - file: a readable file-like object with JSON input
    '''
    lexer = iter(Lexer(file))
    for value in parse_value(lexer):
        yield value
    try:
        lexer.next()
    except common.IncompleteJSONError:
        pass
    else:
        raise common.JSONError('Additional data')

def parse(file):
    '''
    Backend-specific wrapper for ijson.common.parse.
    '''
    return common.parse(basic_parse(file))

def items(file, prefix):
    '''
    Backend-specific wrapper for ijson.common.items.
    '''
    return common.items(parse(file), prefix)
