Unofficial Free Google Translation API
##########################################

``goslate`` provides you *free* access to google translation service by querying google translation website:

- Free: you know it ;)
- Fast: batch, cache and concurrently fetch
- Simple: one file module ``Goslate().translate('Hi', 'zh-CN')``


Usage
======

::

 >>> import goslate
 >>>
 >>> gs = goslate.Goslate()
 >>>
 >>> print gs.translate('hello world', 'de')
 hallo welt

Install
========

.. code-block:: bash
  
  $ pip install goslate

 
or just download `latest goslate.py <./goslate.py>` directly to use it


CLI usage
===========

``goslate.py`` is also a command line tool
    
- Translate ``stdin`` input into Chinese

  .. code-block:: bash
  
     $ echo "hello world" | goslate.py -t zh-CN

- Translate text file(s) into Chinese

  .. code-block:: bash
  
     $ goslate.py -t zh-CN path/to/source-file/a.txt "path to source file b.txt"

     
Feedback
===========     

Report issues & suggestions `here <https://bitbucket.org/zhuoqiang/goslate/issues>`

