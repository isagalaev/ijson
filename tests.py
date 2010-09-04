# -*- coding:utf-8 -*-
import unittest
from cStringIO import StringIO
from decimal import Decimal

from ijson.parse import parse, basic_parse, JSONError
from ijson.utils import ObjectBuilder


JSON = '''
{
  "rows": [
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
      "nested": [[1], [2]]
    }
  ]
}
'''

SCALAR_JSON = '''
"value"
'''

INVALID_JSON = '''
  {"key": "value",}
'''

class Parse(unittest.TestCase):
    def test_basic_parse(self):
        events = list(basic_parse(StringIO(JSON)))
        reference = [
            ('start_map', None),
                ('map_key', 'rows'),
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
                        ('map_key', 'nested'),
                        ('start_array', None),
                            ('start_array', None),
                                ('number', 1),
                            ('end_array', None),
                            ('start_array', None),
                                ('number', 2),
                            ('end_array', None),
                        ('end_array', None),
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
            if prefix == 'rows.item.nested.item.item'
        ]
        self.assertEqual(events, [1, 2])

    def test_scalar(self):
        events = list(parse(StringIO(SCALAR_JSON)))
        self.assertEqual(events, [('', 'string', u'value')])

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
            'rows': [
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
                  'nested': [[1], [2]],
                },
            ],
        })

    def test_scalar_builder(self):
        builder = ObjectBuilder()
        for event, value in basic_parse(StringIO(SCALAR_JSON)):
            builder.event(event, value)
        self.assertEqual(builder.value, u'value')


if __name__ == '__main__':
    unittest.main()
