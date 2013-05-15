#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''
'''

import sys
import os
import unittest
import doctest        
import goslate
import types
import itertools

from goslate import *
from goslate import _MAX_LENGTH_PER_QUERY, _basic_translate, _main

__author__ = 'ZHUO Qiang'
__date__ = '2013-05-14'

class UnitTest(unittest.TestCase):
    def assertIsGenerator(self, generator):
        if not isinstance(generator, types.GeneratorType) and not isinstance(generator, itertools.chain):
            raise self.failureException('type is not generator: %s, %s' % (type(generator), generator))
        
    
    def assertGeneratorEqual(self, expectedResult, generator):
        self.assertIsGenerator(generator)
        self.assertListEqual(list(expectedResult), list(generator))
        
        
    def test__basic_translate(self):
        self.assertEqual((u'', u'en'), _basic_translate('\n \t\n', 'en'))
        
        self.assertEqual((u'hello world.', u'en'), _basic_translate('hello world.', 'en'))
        self.assertEqual((u'你好世界。', u'en'), _basic_translate('hello world.', 'zh-cn'))
        self.assertEqual((u'你好世界。', u'de'), _basic_translate('hallo welt. \n\n', 'zh-CN'))
        self.assertNotEqual(u'你好世界。', _basic_translate('hallo welt.', 'zh-CN', 'en')[0])
        self.assertEqual((u'你好世界。\n\n你好', u'en'), _basic_translate('\n\nhello world.\n\nhello\n\n', 'zh-cn'))

        test_string = 'hello     '
        max_allowed_times = _MAX_LENGTH_PER_QUERY / len(test_string) - 1
        self.assertEqual((u'你好'*max_allowed_times, u'en'), _basic_translate(test_string*max_allowed_times, 'zh'))
        self.assertRaisesRegexp(Error, 'input too large', _basic_translate, test_string*(max_allowed_times+10), 'zh')
        self.assertRaisesRegexp(Error, 'invalid target language', _basic_translate, 'hello', '')
        
        
    def test_translate(self):
        self.assertEqual(u'', translate('\n \n\t\n', 'en'))
        
        self.assertEqual(u'你好世界。', translate('hello world.', 'zh'))
        self.assertEqual(u'你好世界。', translate('hello world.', 'zh-cn', u'en'))
        self.assertEqual(u'你好世界。', translate('hallo welt.', u'zh-CN'))
        self.assertEqual(u'你好世界。', translate(u'hallo welt.', 'zh-CN', 'de'))
        
        self.assertRaisesRegexp(Error, 'invalid target language', translate, '', '')
        
        self.assertNotEqual(u'你好世界。', translate('hallo welt.', u'zh-CN', 'en'))

        test_string = 'helloworld'
        exceed_allowed_times = _MAX_LENGTH_PER_QUERY / len(test_string) + 10
        self.assertRaisesRegexp(Error, 'input too large', translate, test_string*exceed_allowed_times, 'zh')

        self.assertRaisesRegexp(Error, 'invalid target language', translate, 'hello', '')
        
        self.assertEqual(u'你好世界。\n\n你好', translate(u'\n\nhello world.\n\nhello\n\n', 'zh-cn'))

        test_string = u'hello!    '
        exceed_allowed_times = _MAX_LENGTH_PER_QUERY / len(test_string) + 10
        self.assertEqual(u'你好！'*exceed_allowed_times, translate(test_string*exceed_allowed_times, 'zh'))
        
        
        self.assertGeneratorEqual([], translate((), 'en'))        
        self.assertGeneratorEqual([u''], translate(['\n \n\t\n'], 'en'))
        self.assertGeneratorEqual([u'你好世界。'], translate([u'hello world.'], 'zh-cn'))
        self.assertGeneratorEqual([u'你好世界。'], translate(['hello world.'], 'zh-CN', u'en'))
        self.assertGeneratorEqual([u'你好世界。'], translate(['hallo welt.'], u'zh-CN'))
        self.assertGeneratorEqual([u'你好世界。\n\n你好'], translate(['\n\nhello world.\n\nhello\n\n'], 'zh-cn'))
        self.assertNotEqual([u'你好世界。'], translate(['hallo welt.'], 'zh-CN', 'en'))
        self.assertRaisesRegexp(Error, 'invalid target language', translate, [''], u'')
        
        test_string = 'helloworld'
        exceed_allowed_times = _MAX_LENGTH_PER_QUERY / len(test_string) + 1
        self.assertRaisesRegexp(Error, 'input too large', list, translate((u'a', test_string*exceed_allowed_times), 'zh'))


        test_string = 'hello!    '
        exceed_allowed_times = _MAX_LENGTH_PER_QUERY / len(test_string) + 10
        self.assertGeneratorEqual([u'你好！'*exceed_allowed_times]*3, translate((test_string*exceed_allowed_times,)*3, 'zh'))
        self.assertGeneratorEqual([u'你好世界。', u'你好'], translate(['\n\nhello world.\n', '\nhello\n\n'], 'zh-cn'))
        

    def test_detect(self):
        self.assertEqual('en', detect(''))
        self.assertEqual('en', detect('\n\r  \n'))
        self.assertEqual('en', detect('hello world'))
        self.assertEqual('zh-CN', detect('你好世界'))
        self.assertEqual('de', detect(u'hallo welt.'))
        
        self.assertEqual('zh-CN', detect('你好世界'*1000))
        
        self.assertGeneratorEqual(['en', 'zh-CN', 'de', 'en']*10,
                                  detect((u'hello world', '你好世界', u'hallo welt.', '')*10))

        self.assertGeneratorEqual(['en', 'zh-CN', 'de', 'en']*10,
                                  detect(['hello world'*10, u'你好世界'*100, 'hallo welt.'*1000, u'\n\r \t'*1000]*10))


    def test_massive(self):
        times = 1000
        result = translate(('hello world. %s' % i for i in range(times)), 'zh-cn')
        # list(result)
        self.assertGeneratorEqual((u'你好世界。 %s' % i for i in range(times)), result)

        
    def test__main(self):
        import StringIO
        sys.stdin = StringIO.StringIO('hello world')
        sys.stdout = StringIO.StringIO()
        _main([sys.argv[0], 'zh-CN'])
        self.assertEqual(u'你好世界\n', sys.stdout.getvalue())
        

    def test_get_languages(self):
        expected = {
            'el': 'Greek',
            'eo': 'Esperanto',
            'en': 'English',
            'zh': 'Chinese',
            'af': 'Afrikaans',
            'sw': 'Swahili',
            'ca': 'Catalan',
            'it': 'Italian',
            'iw': 'Hebrew',
            'cy': 'Welsh',
            'ar': 'Arabic',
            'ga': 'Irish',
            'cs': 'Czech',
            'et': 'Estonian',
            'gl': 'Galician',
            'id': 'Indonesian',
            'es': 'Spanish',
            'ru': 'Russian',
            'nl': 'Dutch',
            'pt': 'Portuguese',
            'mt': 'Maltese',
            'tr': 'Turkish',
            'lt': 'Lithuanian',
            'lv': 'Latvian',
            'tl': 'Filipino',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'ro': 'Romanian',
            'is': 'Icelandic',
            'pl': 'Polish',
            'yi': 'Yiddish',
            'be': 'Belarusian',
            'fr': 'French',
            'bg': 'Bulgarian',
            'uk': 'Ukrainian',
            'sl': 'Slovenian',
            'hr': 'Croatian',
            'de': 'German',
            'ht': 'Haitian Creole',
            'da': 'Danish',
            'fa': 'Persian',
            'hi': 'Hindi',
            'fi': 'Finnish',
            'hu': 'Hungarian',
            'ja': 'Japanese',
            'zh-TW': 'Chinese (Traditional)',
            'sq': 'Albanian',
            'no': 'Norwegian',
            'ko': 'Korean',
            'sv': 'Swedish',
            'mk': 'Macedonian',
            'sk': 'Slovak',
            'zh-CN': 'Chinese (Simplified)',
            'ms': 'Malay',
            'sr': 'Serbian',}
        self.assertDictEqual(expected, get_languages())
        
        
def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(goslate))
    return tests        
        
if __name__ == '__main__':
    unittest.main()
