#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    README = f.read()


setup(
    name='djangorestframework-filters',
    version='1.0.0.dev1',
    url='http://github.com/philipn/django-rest-framework-filters',
    license='MIT',
    long_description=README,
    description='Better filtering for Django REST Framework',
    author='Philip Neustrom',
    author_email='philipn@gmail.com',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.4',
    install_requires=[
        'djangorestframework',
        'django-filter>=2.0',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
