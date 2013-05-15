#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''
Goslate: unofficial Free Google Translation API
################################################

Goslate provides free access to Google Translation Service through public Google translate web site:

- Free: you know it ;)
- Fast: batch, cache and concurrently fetch. 
- Simple: 3 APIs

  - :func:`translate`
  - :func:`detect`
  - :func:`get_languages`

Example::

 >>> # All APIs are in goslate module
 >>> import goslate
 >>> 
 >>> # You could get all supported language list through get_languages
 >>> languages = goslate.get_languages()
 >>> print languages['en']
 English
 >>>
 >>> # Tranlate the languages' name into Chinese
 >>> language_names = languages.values()
 >>> language_names_in_chinese = goslate.translate(language_names, 'zh')
 >>> 
 >>> # verify each Chinese name is really in Chinese using detect
 >>> language_codes = goslate.detect(language_names_in_chinese)
 >>> for code in language_codes:
 ...         assert 'zh-CN' == code
 ...
 >>>

 
API Reference 
=================================================
 
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

__author__ = 'ZHUO Qiang'
__email__ = 'zhuo.qiang@gmail.com'
__copyright__ = "2013, http://zhuoqiang.me"
__license__ = "MIT"
__date__ = '2013-05-11'
__version_info__ = (1, 0, 0)
__version__ = '.'.join(str(i) for i in __version_info__)
__home__ = 'http://bitbucket.org/zhuoqiang/goslate'

_MAX_LENGTH_PER_QUERY = 1800

_DEBUG = False

_debuglevel = _DEBUG and 1 or 0
_opener = urllib2.build_opener(
    urllib2.HTTPHandler(debuglevel=_debuglevel),
    urllib2.HTTPSHandler(debuglevel=_debuglevel))
    

class Error(Exception):
    '''Error type
    '''
    pass


def _open_url(url):
    if len(url) > _MAX_LENGTH_PER_QUERY+100:
        raise Error('input too large')
    
    # Google forbits urllib2 User-Agent: Python-urllib/2.7
    request = urllib2.Request(url, headers={'User-Agent':'Mozilla/4.0'})
    
    # retry when get (<class 'socket.error'>, error(54, 'Connection reset by peer')
    for i in range(5):
        try:
            response = _opener.open(request, timeout=4)
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
    LEAST_TASK_COUNT_FOR_CONCURRENT = 2
    first_tasks = [next(tasks, None) for i in range(LEAST_TASK_COUNT_FOR_CONCURRENT)]
    tasks = (task for task in itertools.chain(first_tasks, tasks) if task)
    
    if not first_tasks[-1] or not _executor:
        for each in tasks:
            yield each()
    else:
        exception = None
        for each in [_executor.submit(t) for t in tasks]:
            if exception:
                each.cancel()
            else:
                exception = each.exception()
                if not exception:
                    yield each.result()
                    
        if exception:
            raise exception
        
    
def _basic_translate(text, target_language, source_language=''):
    if not target_language:
        raise Error('invalid target language')
    
    if not text.strip():
        return unicode(''), unicode(target_language)

    # Browser request for 'hello world' is:
    # http://translate.google.com/translate_a/t?client=t&hl=en&sl=en&tl=zh-CN&ie=UTF-8&oe=UTF-8&multires=1&prev=conf&psl=en&ptl=en&otf=1&it=sel.2016&ssel=0&tsel=0&prev=enter&oc=3&ssel=0&tsel=0&sc=1&text=hello%20world
    
    GOOGLE_TRASLATE_URL = 'http://translate.google.com/translate_a/t'
    GOOGLE_TRASLATE_PARAMETERS = {
        # 't' client will receiver non-standard json format
        # change client to something other than 't' to get standard json response
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
    translation = u''.join(i['trans'] for i in data['sentences'])
    detected_source_language = data['src']
    return translation, detected_source_language


def get_languages():
    '''Discover supported languages

    It returns iso639-1 language codes for
    `supported languages <https://developers.google.com/translate/v2/using_rest#language-params>`_
    for translation. Some language codes also include a country code, like zh-CN or zh-TW.
    
    .. note:: It only queries Google once for the first time and use cached result afterwards
        
    :returns: a dict of all supported language code and language name mapping ``{'language-code', 'Language name'}``

    Example::

     >>> languages = get_languages()
     >>> assert 'zh' in languages
     >>> print languages['zh']
     Chinese
 
    '''
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

    if 'auto' in languages:
        del languages['auto']
    get_languages.languages = languages
    return languages
        

_SEPERATORS = [urllib.quote_plus(i.encode('utf-8')) for i in
                 u'.!?,;。，？！:："\'“”’‘#$%&()（）*×+/<=>@＃￥[\]…［］^`{|}｛｝～~\n\r\t ']

def _translate_single_text(text, target_language='zh-CN', source_lauguage=''):
    def split_text(text):
        start = 0
        text = urllib.quote_plus(text)
        length = len(text)
        while (length - start) > _MAX_LENGTH_PER_QUERY:
            # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
            for seperator in _SEPERATORS:
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


def translate(text, target_language, source_language=''):
    '''Translate text from source language to target language
    
    .. note::
     - Input all source strings at once. Goslate will batch and fetch concurrently for maximize speed.
     - `futures <https://pypi.python.org/pypi/futures>`_ is required for best performance.
     - It returns generator on batch input in order to better fit pipeline architecture
    
    :param text: The source text(s) to be translated. Batch translation is supported via sequence input
    :type text: UTF-8 str; unicode; string sequence (list, tuple, iterator, generator)
     
    :param target_language: The language to translate the source text into. The value should be one of the language codes listed in :func:`get_languages`
    :type target_language: str; unicode

    :param source_language: The language of the source text. The value should be one of the language codes listed in :func:`get_languages`. If a language is not specified, the system will attempt to identify the source language automatically.
    :type source_language: str; unicode
    
    :returns: the translated text(s)
     - unicode: on single string input
     - generator of unicode: on batch input of string sequence
    
    :raises:
     - :class:`Error` ('invalid target language') if target language is not set
     - :class:`Error` ('input too large') if input a single large word without any punctuation or space in between
    

    Example::

     >>> print translate('hello world', 'de')
     Hallo Welt
     >>> 
     >>> for i in translate(['thank', u'you'], 'de'):
     ...        print i
     ...
     danke
     Sie
     
    '''
    
    if not target_language:
        raise Error('invalid target language')
    
    if not _is_sequence(text):
        return _translate_single_text(unicode(text).encode('utf-8'), target_language, source_language)
    
    JOINT = u'\n\u26ff\n'
    UTF8_JOINT = JOINT.encode('utf-8')
    
    def join_texts(texts):
        texts = (unicode(i).strip().encode('utf-8') for i in texts)
        text = next(texts)
        for i in texts:
            new_text = UTF8_JOINT.join((text, i))
            if len(urllib.quote_plus(new_text)) < _MAX_LENGTH_PER_QUERY:
                text = new_text
            else:
                yield text
                text = i
        yield text
                
        
    def make_task(text):
        return lambda: _translate_single_text(text, target_language, source_language).split(JOINT)
        
    return itertools.chain.from_iterable(_execute(make_task(i) for i in join_texts(text)))


def _detect_language(text):
    if isinstance(text, str):
        text = text.decode('utf-8')
    return _basic_translate(text[:50].encode('utf-8'), 'en')[1]


def detect(text):
    '''Detect language of the input text
    
    .. note::
     - Input all source strings at once. Goslate will detect concurrently for maximize speed.
     - `futures <https://pypi.python.org/pypi/futures>`_ is required for best performance.
     - It returns generator on batch input in order to better fit pipeline architecture.
    
    :param text: The source text(s) whose language you want to identify. Batch detection is supported via sequence input
    :type text: UTF-8 str; unicode; sequence of strings
    :returns:  the language code(s)
     - unicode: on single string input
     - generator of unicode: on batch input of string sequence
    
    :raises: Error if parameter type or value is not valid

    Example::

     >>> print detect('hello world')
     en
     >>> for i in detect([u'hello', 'Hallo']):
     ...        print i
     ...
     en
     de
    
    '''
    if _is_sequence(text):
        return _execute(functools.partial(_detect_language, i) for i in text)
    return _detect_language(text)


def _main(argv):
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
        
    
if __name__ == '__main__':
    try:
        _main(sys.argv)
    except:
        print sys.exc_info()[1]
