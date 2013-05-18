Unofficial Free Google Translation API
##########################################

``goslate`` provides you *free* access to google translation service by querying google translation website:

- Free: you know it ;)
- Fast: batch, cache and concurrently fetch
- Simple: one file module ``Goslate().translate('Hi!', 'zh-CN')``


Usage
======

.. sourcecode:: python

 >>> import goslate
 >>>
 >>> gs = goslate.Goslate()
 >>>
 >>> print gs.translate('hello world', 'de')
 hallo welt

Install
========

.. sourcecode:: bash
  
  $ pip install goslate

 
or just download `latest goslate.py <./goslate.py>`_ directly to use it


CLI usage
===========

``goslate.py`` is also a command line tool
    
- Translate ``stdin`` input into Chinese

  .. sourcecode:: bash
  
     $ echo "hello world" | goslate.py -t zh-CN

- Translate text file(s) into Chinese

  .. sourcecode:: bash
  
     $ goslate.py -t zh-CN path/to/source-file/a.txt "path to source file b.txt"

     
Feedback
===========     

Report issues & suggestions to `tracker at bitbucket <https://bitbucket.org/zhuoqiang/goslate/issues>`_
