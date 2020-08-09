#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    README = f.read()


setup(
    name='djangorestframework-filters',
    version='1.0.0.dev1',
    url='http://github.com/philipn/django-rest-framework-filters',
    description='Better filtering for Django REST Framework',
    long_description=README,
    license_file='LICENSE',
    license='MIT',

    author='Philip Neustrom',
    author_email='philipn@gmail.com',
    maintainer='Ryan P Kilby',
    maintainer_email='kilbyr@gmail.com',

    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.5',
    install_requires=[
        'djangorestframework',
        'django-filter>=2.0',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
