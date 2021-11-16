#! /usr/bin/env sh

# pip install sphinx
# pip install Sphinx-PyPI-upload

python test_goslate.py

# use https://readthedocs.org/ directly
# python setup.py build_sphinx
# python setup.py upload_sphinx
python setup.py bdist_egg upload
python setup.py sdist upload

# for py3 just: python setup.py bdist_egg upload
