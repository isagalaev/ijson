'''
Pure-python parsing backend.
'''
from __future__ import unicode_literals
from decimal import Decimal
import re
from codecs import unicode_escape_decode, getreader

from ijson import common
from ijson.compat import chr


BUFSIZE = 16 * 1024
NONWS = re.compile(r'\S')
LEXTERM = re.compile(r'[\s{}\[\],"]')


class UnexpectedSymbol(common.JSONError):
    def __init__(self, symbol, pos):
        super(UnexpectedSymbol, self).__init__('Unexpected symbol %r at %d' % (symbol, pos))


def Lexer(f, buf_size=BUFSIZE):
    f = getreader('utf-8')(f)
    buf = ''
    pos = 0
    while True:
        match = NONWS.search(buf, pos)
        if match:
            pos = lexemstart = match.start()
            char = buf[pos]
            if char in '[]{},':
                yield lexemstart, char
                pos += 1
            elif char == '"':
                start = pos + 1
                while True:
                    try:
                        end = buf.index('"', start)
                        escpos = end - 1
                        while buf[escpos] == '\\':
                            escpos -= 1
                        if (end - escpos) % 2 == 0:
                            start = end + 1
                        else:
                            break
                    except ValueError:
                        old_len = len(buf)
                        buf += f.read(buf_size)
                        if len(buf) == old_len:
                            raise common.IncompleteJSONError()
                yield lexemstart, buf[pos:end + 1]
                pos = end + 1
            else:
                end = pos
                while True:
                    match = LEXTERM.search(buf, end)
                    if match:
                        end = match.start()
                        break
                    else:
                        end = len(buf)
                        buf += f.read(buf_size)
                        if len(buf) == end:
                            break
                yield lexemstart, buf[pos:end]
                pos = end
        else:
            buf = f.read(buf_size)
            pos = 0
            if not len(buf):
                break


def unescape(s):
    start = 0
    while start < len(s):
        pos = s.find('\\', start)
        if pos == -1:
            yield s[start:]
            break
        yield s[start:pos]
        pos += 1
        esc = s[pos]
        if esc == 'b':
            yield '\b'
        elif esc == 'f':
            yield '\f'
        elif esc == 'n':
            yield '\n'
        elif esc == 'r':
            yield '\r'
        elif esc == 't':
            yield '\t'
        elif esc == 'u':
            yield chr(int(s[pos + 1:pos + 5], 16))
            pos += 4
        else:
            yield esc
        start = pos + 1

def parse_value(lexer, symbol=None, pos=0):
    try:
        if symbol is None:
            pos, symbol = next(lexer)
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
            yield ('string', ''.join(unescape(symbol[1:-1])))
        else:
            try:
                number = Decimal(symbol) if any(c in symbol for c in '.eE') else int(symbol)
                yield ('number', number)
            except ValueError:
                raise UnexpectedSymbol(symbol, pos)
    except StopIteration:
        raise common.IncompleteJSONError()

def parse_array(lexer):
    yield ('start_array', None)
    pos, symbol = next(lexer)
    if symbol != ']':
        while True:
            for event in parse_value(lexer, symbol, pos):
                yield event
            pos, symbol = next(lexer)
            if symbol == ']':
                break
            if symbol != ',':
                raise UnexpectedSymbol(symbol, pos)
            pos, symbol = next(lexer)
    yield ('end_array', None)

def parse_object(lexer):
    yield ('start_map', None)
    pos, symbol = next(lexer)
    if symbol != '}':
        while True:
            if symbol[0] != '"':
                raise UnexpectedSymbol(symbol, pos)
            yield ('map_key', symbol[1:-1])
            pos, symbol = next(lexer)
            if symbol != ':':
                raise UnexpectedSymbol(symbol, pos)
            for event in parse_value(lexer, None, pos):
                yield event
            pos, symbol = next(lexer)
            if symbol == '}':
                break
            if symbol != ',':
                raise UnexpectedSymbol(symbol, pos)
            pos, symbol = next(lexer)
    yield ('end_map', None)

def basic_parse(file=None, buf_size=BUFSIZE):
    '''
    Iterator yielding unprefixed events.

    Parameters:

    - file: a readable file-like object with JSON input
    '''
    lexer = iter(Lexer(file, buf_size))
    for value in parse_value(lexer):
        yield value
    try:
        next(lexer)
    except StopIteration:
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
