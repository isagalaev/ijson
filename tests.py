# -*- coding:utf-8 -*-
import unittest
from cStringIO import StringIO
from decimal import Decimal
import threading

from ijson import parse, basic_parse, JSONError, IncompleteJSONError, ObjectBuilder, items


JSON = r'''
{
  "docs": [
    {
      "string": "\u0441\u0442\u0440\u043e\u043a\u0430",
      "null": null,
      "boolean": false,
      "integer": 0,
      "double": 0.5,
      "long": 10000000000,
      "decimal": 10000000000.5
    },
    {
      "meta": [[1], {}]
    },
    {
      "meta": {"key": "value"}
    },
    {
      "meta": null
    }
  ]
}
'''
SCALAR_JSON = '0'
EMPTY_JSON = ''
INVALID_JSON = '{"key": "value",}'
INCOMPLETE_JSON = '"test'
STRINGS_JSON = r'''
{
    "str1": "",
    "str2": "\"",
    "str3": "\\",
    "str4": "\\\\"
}
'''

class Parse(unittest.TestCase):
    def test_basic_parse(self):
        events = list(basic_parse(StringIO(JSON)))
        reference = [
            ('start_map', None),
                ('map_key', 'docs'),
                ('start_array', None),
                    ('start_map', None),
                        ('map_key', 'string'),
                        ('string', u'строка'),
                        ('map_key', 'null'),
                        ('null', None),
                        ('map_key', 'boolean'),
                        ('boolean', False),
                        ('map_key', 'integer'),
                        ('number', 0),
                        ('map_key', 'double'),
                        ('number', Decimal('0.5')),
                        ('map_key', 'long'),
                        ('number', 10000000000),
                        ('map_key', 'decimal'),
                        ('number', Decimal('10000000000.5')),
                    ('end_map', None),
                    ('start_map', None),
                        ('map_key', 'meta'),
                        ('start_array', None),
                            ('start_array', None),
                                ('number', 1),
                            ('end_array', None),
                            ('start_map', None),
                            ('end_map', None),
                        ('end_array', None),
                    ('end_map', None),
                    ('start_map', None),
                        ('map_key', 'meta'),
                        ('start_map', None),
                            ('map_key', 'key'),
                            ('string', 'value'),
                        ('end_map', None),
                    ('end_map', None),
                    ('start_map', None),
                        ('map_key', 'meta'),
                        ('null', None),
                    ('end_map', None),
                ('end_array', None),
            ('end_map', None),
        ]
        for e, r in zip(events, reference):
            self.assertEqual(e, r)

    def test_parse(self):
        events = parse(StringIO(JSON))
        events = [value
            for prefix, event, value in events
            if prefix == 'docs.item.meta.item.item'
        ]
        self.assertEqual(events, [1])

    def test_scalar(self):
        events = list(parse(StringIO(SCALAR_JSON)))
        self.assertEqual(events, [('', 'number', 0)])

    def test_strings(self):
        events = list(parse(StringIO(STRINGS_JSON)))
        strings = [value for prefix, event, value in events if event == 'string']
        self.assertEqual(strings, ['', '"', '\\', '\\\\'])

    def test_empty(self):
        self.assertRaises(
            IncompleteJSONError,
            lambda: list(parse(StringIO(EMPTY_JSON))),
        )

    def test_incomplete(self):
        self.assertRaises(
            IncompleteJSONError,
            lambda: list(parse(StringIO(INCOMPLETE_JSON))),
        )

    def test_invalid(self):
        self.assertRaises(
            JSONError,
            lambda: list(parse(StringIO(INVALID_JSON))),
        )

    def test_lazy(self):
        # shouldn't fail since iterator is not exhausted
        parse(StringIO(INVALID_JSON))
        self.assertTrue(True)


class Builder(unittest.TestCase):
    def test_object_builder(self):
        builder = ObjectBuilder()
        for event, value in basic_parse(StringIO(JSON)):
            builder.event(event, value)
        self.assertEqual(builder.value, {
            'docs': [
                {
                   'string': u'строка',
                   'null': None,
                   'boolean': False,
                   'integer': 0,
                   'double': Decimal('0.5'),
                   'long': 10000000000,
                   'decimal': Decimal('10000000000.5'),
                },
                {
                    'meta': [[1], {}],
                },
                {
                    'meta': {'key': 'value'},
                },
                {
                    'meta': None,
                },
            ],
        })

    def test_scalar_builder(self):
        builder = ObjectBuilder()
        for event, value in basic_parse(StringIO(SCALAR_JSON)):
            builder.event(event, value)
        self.assertEqual(builder.value, 0)

    def test_items(self):
        meta = list(items(StringIO(JSON), 'docs.item.meta'))
        self.assertEqual(meta, [
            [[1], {}],
            {'key': 'value'},
            None,
        ])

class FuncThread(threading.Thread):
    def __init__(self, func):
        super(FuncThread, self).__init__()
        self.func = func

    def run(self):
        self.func()

class ParseThreaded(Parse):
    def test_basic_parse(self):
        t = FuncThread(super(ParseThreaded, self).test_basic_parse)
        t.start()
        t.join()

    def test_parse(self):
        t = FuncThread(super(ParseThreaded, self).test_parse)
        t.start()
        t.join()

    def test_scalar(self):
        t = FuncThread(super(ParseThreaded, self).test_scalar)
        t.start()
        t.join()

    def test_empty(self):
        t = FuncThread(super(ParseThreaded, self).test_empty)
        t.start()
        t.join()

    def test_incomplete(self):
        t = FuncThread(super(ParseThreaded, self).test_incomplete)
        t.start()
        t.join()

    def test_invalid(self):
        t = FuncThread(super(ParseThreaded, self).test_invalid)
        t.start()
        t.join()

    def test_lazy(self):
        t = FuncThread(super(ParseThreaded, self).test_lazy)
        t.start()
        t.join()

if __name__ == '__main__':
    unittest.main()
