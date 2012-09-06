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
        self.buffer = ''
        self.pos = 0

    def nextsymbol(self):
        while True:
            match = NONWS.search(self.buffer, self.pos)
            if match:
                self.pos = match.start()
                char = self.buffer[self.pos]
                if 'a' <= char <= 'z':
                    return self.readuntil(ALPHATERM)
                elif '0' <= char <= '9' or char == '-':
                    return self.readuntil(NUMTERM)
                else:
                    self.pos += 1
                    return char
            self.buffer = self.f.read(BUFSIZE)
            self.pos = 0
            if not len(self.buffer):
                raise common.IncompleteJSONError()

    def readuntil(self, pattern, escape=None, eatterm=False):
        result = []
        while True:
            match = pattern.search(self.buffer, self.pos)
            if match:
                pos = match.start()
                terminator = self.buffer[pos:pos + 1]
                if terminator == escape:
                    if len(self.buffer) < pos + 2:
                        raise common.IncompleteJSONError()
                    result.append(self.buffer[self.pos:pos + 2])
                    self.pos = pos + 2
                else:
                    result.append(self.buffer[self.pos:pos])
                    self.pos = pos + len(terminator) if eatterm else pos
                    return ''.join(result)
            else:
                result.append(self.buffer[self.pos:])
                self.buffer = self.f.read(BUFSIZE)
                self.pos = 0
                if not self.buffer:
                    if eatterm:
                        raise common.IncompleteJSONError()
                    else:
                        return ''.join(result)

def parse_value(f, symbol=None):
    if symbol == None:
        symbol = f.nextsymbol()
    if symbol == 'null':
        yield ('null', None)
    elif symbol == 'true':
        yield ('boolean', True)
    elif symbol == 'false':
        yield ('boolean', False)
    elif symbol == '"':
        yield ('string', parse_string(f))
    elif symbol == '[':
        for event in parse_array(f):
            yield event
    elif symbol == '{':
        for event in parse_object(f):
            yield event
    else:
        try:
            number = Decimal(symbol) if '.' in symbol else int(symbol)
            yield ('number', number)
        except ValueError:
            raise common.JSONError('Unexpected symbol')

def parse_string(f):
    result = f.readuntil(STRTERM, '\\', eatterm=True)
    return result.decode('unicode-escape')

def parse_array(f):
    yield ('start_array', None)
    expect_comma = False
    while True:
        symbol = f.nextsymbol()
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
        symbol = f.nextsymbol()
        if symbol != '"':
            raise common.JSONError('Unexpected symbol')
        yield ('map_key', parse_string(f))
        symbol = f.nextsymbol()
        if symbol != ':':
            raise common.JSONError('Unexpected symbol')
        for event in parse_value(f):
            yield event
        symbol = f.nextsymbol()
        if symbol == '}':
            break
        if symbol != ',':
            raise common.JSONError('Unexpected symbol')
    yield ('end_map', None)

def basic_parse(f):
    f = Reader(f)
    for value in parse_value(f):
        yield value
    try:
        f.nextsymbol()
    except common.IncompleteJSONError:
        pass
    else:
        raise common.JSONError('Additional data')

def parse(file):
    return common.parse(basic_parse(file))

def items(file, prefix):
    return common.items(basic_parse(file), prefix)
