#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''Goslate, Unofficial Free Google Translate API

- command line arguments for target langauge, source language, encoding setting, proxy
- fix codec error when print on screen
- python3 support
- proxy support
- use only '\n' for joiner
'''

import sys
import os
import urllib2
import urllib
import json
import itertools
import functools
import time
import socket
import xml.etree.ElementTree

__auther__ = 'ZHUO Qiang'
__date__ = '2013-05-11'
__version_info__ = (0, 8, 0)
__version__ = '.'.join(str(i) for i in __version_info__)

_MAX_LENGTH_PER_QUERY = 1900

# set to True to enable debug information
_DEBUG = False
# _DEBUG = True

_debuglevel = _DEBUG and 1 or 0
_opener = urllib2.build_opener(
    urllib2.HTTPHandler(debuglevel=_debuglevel),
    urllib2.HTTPSHandler(debuglevel=_debuglevel))
    

class Error(Exception):
    pass


def _open_url(url):
    if len(url) > _MAX_LENGTH_PER_QUERY+100:
        raise Error('input too large')
    
    # Google forbits urllib2 User-Agent: Python-urllib/2.7
    request = urllib2.Request(url, headers={'User-Agent':'Mozilla/4.0'})
    
    # retry when get (<class 'socket.error'>, error(54, 'Connection reset by peer')
    for i in range(4):
        try:
            response = _opener.open(request)
            response_content = response.read()
            if _DEBUG:
                print response_content
            return response_content
        except socket.error as e:  
            if _DEBUG:
                import threading
                print threading.currentThread(), e
            if 'Connection reset by peer' not in str(e):
                raise e
            time.sleep(0.0001)
    raise e
    

try:
    import concurrent.futures as futures
    _executor = futures.ThreadPoolExecutor(max_workers=120)
except ImportError:
    futures = None
    _executor = None
    
            
def _execute(tasks):
    tasks = list(tasks)
    if len(tasks) < 2 or not _executor:
        return [t() for t in tasks]
    else:
        future_results = [_executor.submit(t) for t in tasks]
        done, not_done = futures.wait(future_results, return_when=futures.FIRST_EXCEPTION)
        if not_done:
            [i.cancel() for i in not_done]
        else:
            return [i.result() for i in future_results]
    
    
def _is_valid_language(language):
    return language.lower() in [i.lower() for i in get_languages().keys()]
        

def _basic_translate(text, target_language, source_language=''):
    if not target_language:
        raise Error('Missing target language')
    
    if not text.strip():
        return unicode(''), unicode(target_language)

    if isinstance(text, unicode):
        text = text.encode('utf-8')
        
    # Browser request for 'hello world' is:
    # http://translate.google.com/translate_a/t?client=t&hl=en&sl=en&tl=zh-CN&ie=UTF-8&oe=UTF-8&multires=1&prev=conf&psl=en&ptl=en&otf=1&it=sel.2016&ssel=0&tsel=0&prev=enter&oc=3&ssel=0&tsel=0&sc=1&text=hello%20world
    
    GOOGLE_TRASLATE_URL = 'http://translate.google.com/translate_a/t'
    GOOGLE_TRASLATE_PARAMETERS = {
        # t client will receiver non-standard json format
        # we change client to something other than t to get the standard json response
        'client': 'z',
        'sl': source_language,
        'tl': target_language,
        'ie': 'UTF-8',
        'oe': 'UTF-8',
        'text': text
        }

    url = '?'.join((GOOGLE_TRASLATE_URL, urllib.urlencode(GOOGLE_TRASLATE_PARAMETERS)))
    response_content = _open_url(url)
    data = json.loads(response_content)
    translation = ''.join(i['trans'] for i in data['sentences'])
    detected_source_language = data['src']
    return translation, detected_source_language


def get_languages():
    # cache
    if hasattr(get_languages, 'languages'):
        return get_languages.languages
    
    GOOGLE_TRASLATOR_URL = 'http://translate.google.com/translate_a/l'
    GOOGLE_TRASLATOR_PARAMETERS = {
        'client': 't',
        }

    url = '?'.join((GOOGLE_TRASLATOR_URL, urllib.urlencode(GOOGLE_TRASLATOR_PARAMETERS)))
    response_content = _open_url(url)
    root = xml.etree.ElementTree.fromstring(response_content)

    if root.tag != 'LanguagePairs':
        return {}
    
    languages = {}
    for i in root.findall('Pair'):
        languages[i.get('target_id')] = i.get('target_name')
        languages[i.get('source_id')] = i.get('source_name')

    languages[''] = languages.get('auto', '')
    get_languages.languages = languages
    return languages
        

def _large_text_translate(text, target_language='zh-CN', source_lauguage=''):
    def split_text(text):
        start = 0
        text = urllib.quote_plus(text)
        length = len(text)
        while (length - start) > _MAX_LENGTH_PER_QUERY:
            for seperator in (urllib.quote_plus(i) for i in ('.', '!', '?', '。', '！', '？', '\n', ',', '，')):
                index = text.rfind(seperator, start, start+_MAX_LENGTH_PER_QUERY)
                if index != -1:
                    break
            else:
                raise Error('input too large')
            end = index + len(seperator)
            yield urllib.unquote_plus(text[start:end])
            start = end
                
        yield urllib.unquote_plus(text[start:])

    def make_task(text):
        return lambda: _basic_translate(text, target_language, source_lauguage)[0]
        
    return ''.join(_execute(make_task(i) for i in split_text(text)))


def _is_sequence(arg):
    return (not isinstance(arg, basestring)) and (
        hasattr(arg, "__getitem__") or hasattr(arg, "__iter__"))


def translate(texts, target_language='zh-CN', source_language=''):
    if not target_language:
        raise Error('missing target language')
    
    if not _is_sequence(texts):
        return _large_text_translate(texts, target_language, source_language)
    
    JOIN = u'\n\u26ff\n'
    UTF8_JOIN = JOIN.encode('utf-8')
    
    def join_texts(texts):
        texts = (i.strip() for i in texts)
        text = next(texts)
        for i in texts:
            new_text = UTF8_JOIN.join((text, i))
            if len(urllib.quote_plus(new_text)) < _MAX_LENGTH_PER_QUERY:
                text = new_text
            else:
                yield text
                text = i
            
        yield text
                
        
    def make_task(text):
        return lambda: _large_text_translate(text, target_language, source_language).split(JOIN)
        
    return itertools.chain(*_execute(make_task(i) for i in join_texts(texts)))


def _detect_language(text):
    if isinstance(text, str):
        text = text.decode('utf-8')
    return _basic_translate(text[:50], 'en')[1]


def detect(texts):
    if _is_sequence(texts):
        return _execute(functools.partial(_detect_language, i) for i in texts)
    return _detect_language(texts)


def main(argv):
    name = os.path.splitext(os.path.basename(argv[0]))[0]
    
    if len(argv) < 2:
        print '''%(name)s %(version)s
text translator using google translation service

usage: %(name)s <target-language> file1 file2 ...
read input from stdin if no file specify
eg. translate README file to Chinese: %(name)s zh-CN ./README
''' % dict(name=name, version=__version__)
        return
    
    target_language = argv[1]
    
    import fileinput
    print '\n'.join(translate(fileinput.input(argv[2:]), target_language))
        
    
# ======================================================================
# Unit test
# ======================================================================
import unittest

class _Tests(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def test__basic_translate(self):
        self.assertEqual((u'', u'en'), _basic_translate('\n \t\n', 'en'))
        
        self.assertEqual((u'hello world.', u'en'), _basic_translate('hello world.', 'en'))
        self.assertEqual((u'你好世界。', u'en'), _basic_translate('hello world.', 'zh-cn'))
        
        # self.assertRaisesRegexp(Error, 'Invalid target language', _basic_translate, '', 'en-US')
        # self.assertRaisesRegexp(Error, 'Invalid source language', _basic_translate, '', 'en', 'en-US')
        
        self.assertEqual((u'你好世界。', u'de'), _basic_translate('hallo welt. \n\n', 'zh-CN'))
        
        self.assertNotEqual((u'你好世界。', u'en'), _basic_translate('hallo welt.', 'zh-CN', 'en'))

        test_string = 'hello     '
        max_allowed_times = _MAX_LENGTH_PER_QUERY / len(test_string) - 1
        self.assertEqual((u'你好'*max_allowed_times, u'en'), _basic_translate(test_string*max_allowed_times, 'zh'))

        self.assertRaisesRegexp(Error, 'input too large', _basic_translate, test_string*(max_allowed_times+10), 'zh')
        self.assertRaises(Error, _basic_translate, 'hello', '')

        self.assertEqual((u'你好世界。\n\n你好', u'en'), _basic_translate('\n\nhello world.\n\nhello\n\n', 'zh-cn'))
        
        
    def test__large_text_translate(self):
        self.assertEqual(u'', _large_text_translate('\n \n\t\n', 'en'))
        
        self.assertEqual(u'你好世界。', _large_text_translate('hello world.', 'zh-cn'))
        self.assertEqual(u'你好世界。', _large_text_translate('hello world.', 'zh-CN', 'en'))
        self.assertEqual(u'你好世界。', _large_text_translate('hallo welt.', 'zh-CN'))
        
        # self.assertRaisesRegexp(Error, 'Invalid target language', translate, '', 'en-US')
        # self.assertRaisesRegexp(Error, 'Invalid source language', translate, '', 'en', 'en-US')
        
        self.assertNotEqual(u'你好世界。', _large_text_translate('hallo welt.', 'zh-CN', 'en'))

        test_string = 'hello     '
        exceed_allowed_times = _MAX_LENGTH_PER_QUERY / len(test_string) + 1
        self.assertRaisesRegexp(Error, 'input too large', _large_text_translate, test_string*exceed_allowed_times, 'zh')

        self.assertRaises(Error, _large_text_translate, 'hello', '')
        
        self.assertEqual(u'你好世界。\n\n你好', _large_text_translate('\n\nhello world.\n\nhello\n\n', 'zh-cn'))

        test_string = 'hello!    '
        exceed_allowed_times = _MAX_LENGTH_PER_QUERY / len(test_string) + 10
        self.assertEqual(u'你好！'*exceed_allowed_times, _large_text_translate(test_string*exceed_allowed_times, 'zh'))
        
        
    def test_translate(self):
        self.assertListEqual([u''], list(translate(['\n \n\t\n'], 'en')))
        
        self.assertListEqual([u'你好世界。'], list(translate(['hello world.'], 'zh-cn')))
        self.assertEqual(u'你好世界。', translate('hello world.', 'zh-cn'))        
        self.assertListEqual([u'你好世界。'], list(translate(['hello world.'], 'zh-CN', 'en')))
        self.assertListEqual([u'你好世界。'], list(translate(['hallo welt.'], 'zh-CN')))
        
        self.assertNotEqual([u'你好世界。'], list(translate(['hallo welt.'], 'zh-CN', 'en')))

        # self.assertRaisesRegexp(Error, 'Invalid target language', translate, [''], 'en-US')
        # self.assertRaisesRegexp(Error, 'Invalid source language', translate, [''], 'en', 'en-US')
        
        test_string = 'hello     '
        exceed_allowed_times = _MAX_LENGTH_PER_QUERY / len(test_string) + 1
        self.assertRaisesRegexp(Error, 'input too large', translate, [test_string*exceed_allowed_times], 'zh')

        self.assertRaises(Error, translate, ['hello'], '')
        
        self.assertListEqual([u'你好世界。\n\n你好'], list(translate(['\n\nhello world.\n\nhello\n\n'], 'zh-cn')))

        test_string = 'hello!    '
        exceed_allowed_times = _MAX_LENGTH_PER_QUERY / len(test_string) + 10
        self.assertListEqual([u'你好！'*exceed_allowed_times], list(translate([test_string*exceed_allowed_times], 'zh')))
        
        self.assertListEqual(
            [u'你好世界。 %s' % i for i in range(400)],
            list(translate(['hello world. %s' % i for i in range(400)], 'zh-cn')))

        self.assertListEqual([u'你好世界。', u'你好'], list(translate(['\n\nhello world.\n', '\nhello\n\n'], 'zh-cn')))
        

    def test__detect_lauguage(self):
        self.assertEqual('en', _detect_language('hello world'))
        self.assertEqual('zh-CN', _detect_language('你好世界'))
        self.assertEqual('de', _detect_language('hallo welt.'))
        self.assertEqual('en', _detect_language('hello world'))        
        
        self.assertEqual('zh-CN', _detect_language('你好世界'*1000))
        
    def test_detect(self):
        self.assertListEqual(['en', 'zh-CN', 'de', 'en']*10,
                             list(detect(['hello world', '你好世界',
                                          'hallo welt.', 'hello world']*10)))

        self.assertListEqual(['en', 'zh-CN', 'de', 'en']*10,
                             list(detect(['hello world'*10,
                                          '你好世界'*100, 'hallo welt.'*1000,
                                          'hello world'*1000]*10)))


    def test_massive(self):
        translate(['hello world. %s' % i for i in range(1000)], 'zh-cn')

    def test_main(self):
        import StringIO
        sys.stdin = StringIO.StringIO('hello world')
        sys.stdout = StringIO.StringIO()
        main([sys.argv[0], 'zh-CN'])
        self.assertEqual(u'你好世界\n', sys.stdout.getvalue())
        

    def test_get_languages(self):
        expected = {
            '': 'Detect language',
            'auto': 'Detect language',
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
        
        
if __name__ == '__main__':
    try:
        main(sys.argv)
    except:
        print sys.exc_info()[1]
