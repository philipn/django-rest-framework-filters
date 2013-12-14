`django-rest-framework-chain` is an extension to Django REST Framework that allows arbitrary chaining of both relations and lookup filters.

.. image:: https://secure.travis-ci.org/philipn/django-rest-framework-chain.png?branch=master
   :target: http://travis-ci.org/philipn/django-rest-framework-chain

Installation
------------

.. code-block:: bash

    $ pip install djangorestframework-chain

Requirements
------------

* Python 2.6+
* Django 1.4.5+

Usage
-----

Chaining filtering through relations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To enable chained filtering through relations:

*views.py*

.. code-block:: python

    from rest_framework import viewsets
    import django_filters
    from rest_framework_chain import ChainedFilterSet, RelatedFilter

    class PageFilter(ChainedFilterSet):
        title = django_filters.CharFilter(name='title')
        author = RelatedFilter(UserFilter, name='author')

    # Just a regular FilterSet
    class UserFilter(django_filters.FilterSet):
        username = django_filters.CharFilter(name='username')
        ...

    # Then just use the PageFilter as you would any other FilterSet:

    class PageView(viewsets.ModelViewSet):
        ...
        filter_class = PageFilter

then we can automatically chain our filters through the ``author`` relation, as so::

    /api/page/?author__username=philipn


Allowing any lookup type on a field
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can use the ``AllLookupsFilter`` to allow all possible lookup types on a particular
field.  While we could otherwise specify these by hand, e.g.:

.. code-block:: python

    class ProductFilter(django_filters.FilterSet):
        min_price = django_filters.NumberFilter(name="price", lookup_type='gte')
        ...

to allow the ``price__gte`` lookup.  But this gets cumbersome, and we sometimes want to
allow any possible lookups on particular fields.  We do this by using ``AllLookupsFilter``:

*views.py*

.. code-block:: python

    from rest_framework import viewsets
    import django_filters
    from rest_framework_chain import ChainedFilterSet, AllLookupsFilter

    class PageFilter(ChainedFilterSet):
        title = AllLookupsFilter(name='title')
        ...

then we can use any possible lookup on the ``title`` field, e.g.::

    /api/page/?title__icontains=park

or ::

    /api/page/?title__startswith=The

and also filter on the default lookup (``exact``), as usual::

    /api/page/?title=The%20Park

Combining RelatedFilter and AllLookupsFilter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can combine ``RelatedFilter`` and ``AllLookupsFilter``:

.. code-block:: python

    from rest_framework import viewsets
    import django_filters
    from rest_framework_chain import ChainedFilterSet, RelatedFilter

    class PageFilter(ChainedFilterSet):
        title = django_filters.CharFilter(name='title')
        author = RelatedFilter(UserFilter, name='author')

    # Just a regular FilterSet
    class UserFilter(ChainedFilterSet):
        username = AllLookupsFilter(name='username')
        ...

then we can filter like so::

    /api/page/?author__username__icontains=john

More information on RelatedFilter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Recursive relations are supported.  You will need to specify the full module
path in the ``RelatedFilter`` definition in some cases, e.g.:

.. code-block:: python

   class PersonFilter(ChainedFilterSet):
    name = AllLookupsFilter(name='name')
    best_friend = RelatedFilter('people.views.PersonFilter', name='best_friend')

    class Meta:
        model = Person 

License
-------
Copyright (c) 2013 Philip Neustrom <philipn@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
