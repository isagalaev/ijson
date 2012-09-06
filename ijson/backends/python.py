from decimal import Decimal
import re

from ijson import common


BUFSIZE = 4 * 1024
NONWS = re.compile(r'\S')
STRTERM = re.compile(r'["\\]')
NUMTERM = re.compile(r'[^0-9\.-]')
ALPHATERM = re.compile(r'[^a-z]')


class Reader(object):
    def __init__(self, f):
        self.f = f

    def __iter__(self):
        self.buffer = ''
        self.pos = 0
        return self

    def next(self):
        while True:
            match = NONWS.search(self.buffer, self.pos)
            if match:
                self.pos = match.start()
                char = self.buffer[self.pos]
                if 'a' <= char <= 'z':
                    return self.lexem(ALPHATERM)
                elif '0' <= char <= '9' or char == '-':
                    return self.lexem(NUMTERM)
                elif char == '"':
                    self.pos += 1
                    return '"' + self.stringlexem()
                else:
                    self.pos += 1
                    return char
            self.buffer = self.f.read(BUFSIZE)
            self.pos = 0
            if not len(self.buffer):
                raise common.IncompleteJSONError()

    def lexem(self, pattern):
        result = []
        while True:
            match = pattern.search(self.buffer, self.pos)
            if match:
                pos = match.start()
                result.append(self.buffer[self.pos:pos])
                self.pos = pos
                break
            result.append(self.buffer[self.pos:])
            self.buffer = self.f.read(BUFSIZE)
            self.pos = 0
            if not self.buffer:
                break
        return ''.join(result)

    def stringlexem(self):
        result = []
        while True:
            match = STRTERM.search(self.buffer, self.pos)
            if match:
                pos = match.start()
                if self.buffer[pos] == '\\':
                    if len(self.buffer) < pos + 2:
                        raise common.IncompleteJSONError()
                    result.append(self.buffer[self.pos:pos + 2])
                    self.pos = pos + 2
                else:
                    pos += 1 # ending quote
                    result.append(self.buffer[self.pos:pos])
                    self.pos = pos
                    break
            else:
                result.append(self.buffer[self.pos:])
                self.buffer = self.f.read(BUFSIZE)
                self.pos = 0
                if not self.buffer:
                    raise common.IncompleteJSONError()
        return ''.join(result)

def parse_value(f, symbol=None):
    if symbol == None:
        symbol = f.next()
    if symbol == 'null':
        yield ('null', None)
    elif symbol == 'true':
        yield ('boolean', True)
    elif symbol == 'false':
        yield ('boolean', False)
    elif symbol == '[':
        for event in parse_array(f):
            yield event
    elif symbol == '{':
        for event in parse_object(f):
            yield event
    elif symbol[0] == '"':
        yield ('string', symbol.strip('"').decode('unicode-escape'))
    else:
        try:
            number = Decimal(symbol) if '.' in symbol else int(symbol)
            yield ('number', number)
        except ValueError:
            raise common.JSONError('Unexpected symbol')

def parse_array(f):
    yield ('start_array', None)
    expect_comma = False
    while True:
        symbol = f.next()
        if symbol == ']':
            break
        if expect_comma:
            if symbol != ',':
                raise common.JSONError('Unexpected symbol')
        else:
            for event in parse_value(f, symbol):
                yield event
        expect_comma = not expect_comma
    yield ('end_array', None)

def parse_object(f):
    yield ('start_map', None)
    while True:
        symbol = f.next()
        if symbol[0] != '"':
            raise common.JSONError('Unexpected symbol')
        yield ('map_key', symbol.strip('"'))
        symbol = f.next()
        if symbol != ':':
            raise common.JSONError('Unexpected symbol')
        for event in parse_value(f):
            yield event
        symbol = f.next()
        if symbol == '}':
            break
        if symbol != ',':
            raise common.JSONError('Unexpected symbol')
    yield ('end_map', None)

def basic_parse(f):
    f = iter(Reader(f))
    for value in parse_value(f):
        yield value
    try:
        f.next()
    except common.IncompleteJSONError:
        pass
    else:
        raise common.JSONError('Additional data')

def parse(file):
    return common.parse(basic_parse(file))

def items(file, prefix):
    return common.items(basic_parse(file), prefix)
