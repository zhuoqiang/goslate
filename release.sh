#! /usr/bin/env sh

# pip install sphinx
# pip install Sphinx-PyPI-upload

# pip install twine

python test_goslate.py

# use https://readthedocs.org/ directly
# python setup.py build_sphinx
# python setup.py upload_sphinx
rm -rf dist/*
python setup.py bdist_egg upload
python setup.py sdist upload
twine upload dist/*

# for py3 just: python setup.py bdist_egg upload
