Unofficial Free Google Translation API
##########################################

.. contents:: :local:

``goslate`` provides you *free* access to google translation service by querying google translation website.

It is:

- **Free**: you know it ;)
- **Fast**: batch, cache and concurrently fetch
- **Simple**: single file module, just ``Goslate().translate('Hi!', 'zh-CN')``


Usage
======

.. sourcecode:: python

 >>> import goslate
 >>> gs = goslate.Goslate()
 >>> print gs.translate('hello world', 'de')
 hallo welt

 
Check `API reference <http://pythonhosted.org/goslate/#id7>`_ for more functions
 
 
Install
========

.. sourcecode:: bash
  
  $ pip install goslate

 
or just download `latest goslate.py <https://bitbucket.org/zhuoqiang/goslate/raw/tip/goslate.py>`_ directly and use

`futures <https://pypi.python.org/pypi/futures>`_ is optional but recommended to install for best performance.


CLI
===========

``goslate.py`` is also a command line tool
    
- Translate ``stdin`` input into Chinese

  .. sourcecode:: bash
  
     $ echo "hello world" | goslate.py -t zh-CN

- Translate text file(s) into Chinese, output to UTF-8 file

  .. sourcecode:: bash
  
     $ goslate.py -t zh-CN source/file/a.txt "source file b.txt" > output.txt

     
Contribute
===========     

- Report `issues & suggestions <https://bitbucket.org/zhuoqiang/goslate/issues>`_
- Fork `repository <https://bitbucket.org/zhuoqiang/goslate>`_
- `Donation <http://pythonhosted.org/goslate/#id9>`_
