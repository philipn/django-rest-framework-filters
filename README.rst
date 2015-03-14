``django-rest-framework-filters`` (formerly ``django-rest-framework-chain``) is an extension to Django REST Framework that makes working with filtering much easier.  In addition to fixing some underlying warts and limitations of ``django-filter``, we allow arbitrary chaining of both relations and lookup filters.

E.g. using ``django-rest-framework-filters`` instead of just ``django-filter``, we can do stuff like::

    /api/page/?author__username__icontains=john
    /api/page/?author__username__endswith=smith

Without having to create a zillion filter fields by hand.

.. image:: https://secure.travis-ci.org/philipn/django-rest-framework-filters.png?branch=master
   :target: http://travis-ci.org/philipn/django-rest-framework-filters

Installation
------------

.. code-block:: bash

    $ pip install djangorestframework-filters

Requirements
------------

* Python 2.6+
* Django 1.4.5+

Usage
-----

Here's how you were probably doing filtering before:

.. code-block:: python

    import django_filters
    from myapp.models import Product
    
    class ProductFilter(django_filters.FilterSet):
        manufacturer = django_filters.CharFilter(name="manufacturer__name")
    
        class Meta:
            model = Product
            fields = ['category', 'in_stock', 'manufacturer']


To use ``django-rest-framework-filters``, simply import ``rest_framework_filters`` instead of
``django_filters``:

.. code-block:: python

    import rest_framework_filters as filters
    from myapp.models import Product
    
    class ProductFilter(filters.FilterSet):
        manufacturer = filters.CharFilter(name="manufacturer__name")
    
        class Meta:
            model = Product
            fields = ['category', 'in_stock', 'manufacturer']

All filters found in ``django-filter`` are available for usage.  In this case, there's nothing new
that's gained.  But read onward!


Chaining filtering through relations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To enable chained filtering through relations:

.. code-block:: python

    from rest_framework import viewsets
    import rest_framework_filters as filters

    class UserFilter(filters.FilterSet):
        username = filters.CharFilter(name='username')
        ...

    class PageFilter(filters.FilterSet):
        title = filters.CharFilter(name='title')
        author = filters.RelatedFilter(UserFilter, name='author')
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

    class ProductFilter(filters.FilterSet):
        min_price = filters.NumberFilter(name="price", lookup_type='gte')
        ...

to allow the ``price__gte`` lookup.  But this gets cumbersome, and we sometimes want to
allow any possible lookups on particular fields.  We do this by using ``AllLookupsFilter``:

.. code-block:: python

    from rest_framework import viewsets
    import rest_framework_filters as filters

    class PageFilter(filters.FilterSet):
        title = filters.AllLookupsFilter(name='title')
        ...

then we can use any possible lookup on the ``title`` field, e.g.::

    /api/page/?title__icontains=park

or ::

    /api/page/?title__startswith=The

and also filter on the default lookup (``exact``), as usual::

    /api/page/?title=The%20Park

Combining RelatedFilter and AllLookupsFilter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can combine ``RelatedFilter`` and ``AllLookupsFilter``:

.. code-block:: python

    from rest_framework import viewsets
    import rest_framework_filters as filters

    class PageFilter(filters.FilterSet):
        title = filters.CharFilter(name='title')
        author = filters.RelatedFilter(UserFilter, name='author')

    class UserFilter(filters.FilterSet):
        username = AllLookupsFilter(name='username')
        ...

then we can filter like so::

    /api/page/?author__username__icontains=john

DjangoFilterBackend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We implement our own subclass of ``DjangoFilterBackend``, which you should probably use instead
of the default ``DjangoFilterBackend``.  Our ``DjangoFilterBackend`` caches repeated filter set
generation — a particularly important optimization when using ``RelatedFilter`` and ``AllLookupsFilter``.

To use our ``FilterBackend``, in your `settings.py``, simply use:

.. code-block:: python

    REST_FRAMEWORK = {
        ...
        'DEFAULT_FILTER_BACKENDS': (
            'rest_framework_filters.backends.DjangoFilterBackend', ...
        ),

instead of the default ``rest_framework.filters.DjangoFilterBackend``.

What warts are fixed?
~~~~~~~~~~~~~~~~~~~~~

Even if you're not using ``RelatedFilter`` or ``AllLookupsFilter``, you will probably want
to use ``django-rest-framework-filters``.  For instance, if you simply use ``django-filter``
it is very difficult to filter on a ``DateTimeFilter`` in the date format emitted by
the default serializer (ISO 8601), which makes working with your API difficult.

Can I mix and match `django-filter` and `django-rest-framework-filters`?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes you can.  `django-rest-framework-filters` extends `django-filter`, and you can mix and match them as you please.  For a given class, you should use only one of ``django-filter`` or
``django-rest-framework-filters``, but you can use ``RelatedFilter`` to
link to a filter relation defined elsewhere that uses vanilla ``django-filter``.

More information on RelatedFilter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Recursive relations are supported.  You will need to specify the full module
path in the ``RelatedFilter`` definition in some cases, e.g.:

.. code-block:: python

    class PersonFilter(filters.FilterSet):
        name = filters.AllLookupsFilter(name='name')
        best_friend = filters.RelatedFilter('people.views.PersonFilter', name='best_friend')

        class Meta:
            model = Person 

Wanted functionality
~~~~~~~~~~~~~~~~~~~~

  * Better support for ``__in=``.
  * Allow for ``OR`` as well as ``AND`` style filtering.

License
-------
Copyright (c) 2013-2015 Philip Neustrom <philipn@gmail.com>

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
