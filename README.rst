:mod:`goslate`: unofficial Free Google Translation API
########################################################

:mod:`goslate` provides you *free* access to google translation service by querying google translation website interface

.. :download:`download test.py <test.py>`

- Free: you know it ;)
- Fast: batch, cache and concurrently fetch. 
- Simple: 3 APIs

  - :func:`goslate.translate`
  - :func:`goslate.detect`
  - :func:`goslate.get_languages`
  
It could also be used as a command line tool directly
    
- Translate text into Chinese. read source text from stdin, output to stdout

  .. code-block:: bash
  
     $ echo "hello world" | goslate.py -t zh-CN

- Translate text file(s) into Chinese. output to stdout

  .. code-block:: bash
  
     $ goslate.py -t zh-CN path/to/source-file/a.txt "path to source file b.txt"
    
  
Reference 
=================

.. automodule:: goslate
   :members: 

   
Todo   
=================
- proxy support
- python3 support
- ignore encoding error when print on screen
- add command line arguments for encoding setting, proxy
