from decimal import Decimal
import re

from ijson import common


BUFSIZE = 4 * 1024
NONWS = re.compile(r'\S')
STRTERM = re.compile(r'["\\]')
NUMTERM = re.compile(r'[^0-9\.]')


class Reader(object):
    def __init__(self, f):
        self.f = f
        self.buffer = ''
        self.pos = 0

    def read(self, count):
        if count <= len(self.buffer) - self.pos:
            start = self.pos
            self.pos += count
            return self.buffer[start:self.pos]
        else:
            over = count - (len(self.buffer) - self.pos)
            self.newbuffer = self.f.read(BUFSIZE)
            result = self.buffer[self.pos:] + self.newbuffer[:over]
            self.buffer = self.newbuffer
            self.pos = over
            return result

    def retract(self):
        self.pos -= 1
        assert self.pos >= 0

    def nextchar(self):
        while True:
            match = NONWS.search(self.buffer, self.pos)
            if match:
                self.pos = match.start() + 1
                return self.buffer[match.start()]
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

def parse_value(f):
    char = f.nextchar()
    if char == 'n':
        if f.read(3) != 'ull':
            raise common.JSONError('Unexpected symbol')
        yield ('null', None)
    elif char == 't':
        if f.read(3) != 'rue':
            raise common.JSONError('Unexpected symbol')
        yield ('boolean', True)
    elif char == 'f':
        if f.read(4) != 'alse':
            raise common.JSONError('Unexpected symbol')
        yield ('boolean', False)
    elif char == '-' or ('0' <= char <= '9'):
        number = char + f.readuntil(NUMTERM)
        try:
            number = Decimal(number) if '.' in number else int(number)
        except ValueError:
            raise common.JSONError('Unexpected symbol')
        yield ('number', number)
    elif char == '"':
        yield ('string', parse_string(f))
    elif char == '[':
        for event in parse_array(f):
            yield event
    elif char == '{':
        for event in parse_object(f):
            yield event
    else:
        raise common.JSONError('Unexpected symbol')

def parse_string(f):
    result = f.readuntil(STRTERM, '\\', eatterm=True)
    return result.decode('unicode-escape')

def parse_array(f):
    yield ('start_array', None)
    char = f.nextchar()
    if char != ']':
        f.retract()
        while True:
            for event in parse_value(f):
                yield event
            char = f.nextchar()
            if char == ']':
                break
            if char != ',':
                raise common.JSONError('Unexpected symbol')
    yield ('end_array', None)

def parse_object(f):
    yield ('start_map', None)
    while True:
        char = f.nextchar()
        if char != '"':
            raise common.JSONError('Unexpected symbol')
        yield ('map_key', parse_string(f))
        char = f.nextchar()
        if char != ':':
            raise common.JSONError('Unexpected symbol')
        for event in parse_value(f):
            yield event
        char = f.nextchar()
        if char == '}':
            break
        if char != ',':
            raise common.JSONError('Unexpected symbol')
    yield ('end_map', None)

def basic_parse(f):
    f = Reader(f)
    for value in parse_value(f):
        yield value
    try:
        f.nextchar()
    except common.IncompleteJSONError:
        pass
    else:
        raise common.JSONError('Additional data')

def parse(file):
    return common.parse(basic_parse(file))

def items(file, prefix):
    return common.items(basic_parse(file), prefix)
