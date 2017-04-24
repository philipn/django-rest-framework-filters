Django Rest Framework Filters
=============================

.. image:: https://travis-ci.org/philipn/django-rest-framework-filters.png?branch=master
  :target: https://travis-ci.org/philipn/django-rest-framework-filters

.. image:: https://codecov.io/gh/philipn/django-rest-framework-filters/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/philipn/django-rest-framework-filters

.. image:: https://img.shields.io/pypi/v/djangorestframework-filters.svg
  :target: https://pypi.python.org/pypi/djangorestframework-filters


``django-rest-framework-filters`` is an extension to `Django REST framework`_ and `Django filter`_
that makes it easy to filter across relationships. Historically, this extension also provided a
number of additional features and fixes, however the number of features has shrunk as they are
merged back into ``django-filter``.

.. _`Django REST framework`: https://github.com/tomchristie/django-rest-framework
.. _`Django filter`: https://github.com/carltongibson/django-filter

Using ``django-rest-framework-filters``, we can easily do stuff like::

    /api/article?author__first_name__icontains=john
    /api/article?is_published!=true

.. contents::
    **Table of Contents**
    :local:
    :depth: 2
    :backlinks: none

Features
--------

* Easy filtering across relationships
* Support for method filtering across relationships
* Automatic filter negation with a simple ``param!=value`` syntax
* Backend caching to increase performance


Requirements
------------

* **Python**: 2.7 or 3.3+
* **Django**: 1.8, 1.9, 1.10, 1.11
* **DRF**: 3.5, 3.6


Installation
------------

.. code-block:: bash

    $ pip install djangorestframework-filters


Usage
-----

Upgrading from ``django-filter`` to ``django-rest-framework-filters`` is straightforward:

* Import from ``rest_framework_filters`` instead of from ``django_filters``
* Use the ``rest_framework_filters`` backend instead of the one provided by ``django_filter``.

.. code-block:: python

    # django-filter
    from django_filters.rest_framework import FilterSet, filters

    class ProductFilter(FilterSet):
        manufacturer = filters.ModelChoiceFilter(queryset=Manufacturer.objects.all())
        ...


    # django-rest-framework-filters
    import rest_framework_filters as filters

    class ProductFilter(filters.FilterSet):
        manufacturer = filters.ModelChoiceFilter(queryset=Manufacturer.objects.all())
        ...


To use the django-rest-framework-filters backend, add the following to your settings:

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_FILTER_BACKENDS': (
            'rest_framework_filters.backends.DjangoFilterBackend', ...
        ),
        ...


Once configured, you can continue to use all of the filters found in ``django-filter``.


Filtering across relationships
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can easily traverse multiple relationships when filtering by using ``RelatedFilter``:

.. code-block:: python

    from rest_framework import viewsets
    import rest_framework_filters as filters


    class ManagerFilter(filters.FilterSet):
        class Meta:
            model = Manager
            fields = {'name': ['exact', 'in', 'startswith']}


    class DepartmentFilter(filters.FilterSet):
        manager = filters.RelatedFilter(ManagerFilter, name='manager', queryset=Manager.objects.all())

        class Meta:
            model = Department
            fields = {'name': ['exact', 'in', 'startswith']}


    class CompanyFilter(filters.FilterSet):
        department = filters.RelatedFilter(DepartmentFilter, name='department', queryset=Department.objects.all())

        class Meta:
            model = Company
            fields = {'name': ['exact', 'in', 'startswith']}


    # company viewset
    class CompanyView(viewsets.ModelViewSet):
        filter_class = CompanyFilter
        ...

Example filter calls:

.. code-block::

    /api/companies?department__name=Accounting
    /api/companies?department__manager__name__startswith=Bob

``queryset`` callables
""""""""""""""""""""""

Since ``RelatedFilter`` is a subclass of ``ModelChoiceFilter``, the ``queryset`` argument supports callable behavior.
In the following example, the set of departments is restricted to those in the user's company.

.. code-block:: python

    def departments(request):
        company = request.user.company
        return company.department_set.all()

    class EmployeeFilter(filters.FilterSet):
        department = filters.RelatedFilter(filterset=DepartmentFilter, queryset=departments)
        ...

Recursive relationships
"""""""""""""""""""""""

Recursive relations are also supported. It may be necessary to specify the full module path.

.. code-block:: python

    class PersonFilter(filters.FilterSet):
        name = filters.AllLookupsFilter(name='name')
        best_friend = filters.RelatedFilter('people.views.PersonFilter', name='best_friend', queryset=Person.objects.all())

        class Meta:
            model = Person

Supporting ``Filter.method``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``django_filters.MethodFilter`` has been deprecated and reimplemented as the ``method`` argument
to all filter classes. It incorporates some of the implementation details of the old
``rest_framework_filters.MethodFilter``, but requires less boilerplate and is simpler to write.

* It is no longer necessary to perform empty/null value checking.
* You may use any filter class (``CharFilter``, ``BooleanFilter``, etc...) which will
  validate input values for you.
* The argument signature has changed from ``(name, qs, value)`` to ``(qs, name, value)``.

.. code-block:: python

    class PostFilter(filters.FilterSet):
        # Note the use of BooleanFilter, the original model field's name, and the method argument.
        is_published = filters.BooleanFilter(name='date_published', method='filter_is_published')

        class Meta:
            model = Post
            fields = ['title', 'content']

        def filter_is_published(self, qs, name, value):
            """
            `is_published` is based on the `date_published` model field.
            If the publishing date is null, then the post is not published.
            """
            # incoming value is normalized as a boolean by BooleanFilter
            isnull = not value
            lookup_expr = LOOKUP_SEP.join([name, 'isnull'])

            return qs.filter(**{lookup_expr: isnull})

    class AuthorFilter(filters.FilterSet):
        posts = filters.RelatedFilter('PostFilter', queryset=Post.objects.all())

        class Meta:
            model = Author
            fields = ['name']

The above would enable the following filter calls:

.. code-block::

    /api/posts?is_published=true
    /api/authors?posts__is_published=true


In the first API call, the filter method receives a queryset of posts. In the second,
it receives a queryset of users. The filter method in the example modifies the lookup
name to work across the relationship, allowing you to find published posts, or authors
who have published posts.

Automatic Filter Negation/Exclusion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FilterSets support automatic exclusion using a simple ``param!=value`` syntax. This syntax
internally sets the ``exclude`` property on the filter.

.. code-block::

    /api/page?title!=The%20Park

This syntax supports regular filtering combined with exclusion filtering. For example, the
following would search for all articles containing "Hello" in the title, while excluding
those containing "World".

.. code-block::

    /api/articles?title__contains=Hello&title__contains!=World

Note that most filters only accept a single query parameter. In the above, ``title__contains``
and ``title__contains!`` are interpreted as two separate query parameters. The following would
probably be invalid, although it depends on the specifics of the individual filter class:

.. code-block::

    /api/articles?title__contains=Hello&title__contains!=World&title_contains!=Friend


Allowing any lookup type on a field
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need to enable several lookups for a field, django-filter provides the dict-syntax for
``Meta.fields``.

.. code-block:: python

    class ProductFilter(filters.FilterSet):
        class Meta:
            model = Product
            fields = {
                'price': ['exact', 'lt', 'gt', ...],
            }

``django-rest-framework-filters`` also allows you to enable all possible lookups for any field.
This can be achieved through the use of ``AllLookupsFilter`` or using the ``'__all__'`` value in
the ``Meta.fields`` dict-style syntax. Generated filters (``Meta.fields``, ``AllLookupsFilter``)
will never override your declared filters.

Note that using all lookups comes with the same admonitions as enabling ``'__all__'`` fields in
django forms (`docs`_). Exposing all lookups may allow users to construct queries that
inadvertently leak data. Use this feature responsibly.

.. _`docs`: https://docs.djangoproject.com/en/1.10/topics/forms/modelforms/#selecting-the-fields-to-use

.. code-block:: python

    class ProductFilter(filters.FilterSet):
        # Not overridden by `__all__`
        price__gt = filters.NumberFilter(name='price', lookup_expr='gt', label='Minimum price')

        class Meta:
            model = Product
            fields = {
                'price': '__all__',
            }

    # or

    class ProductFilter(filters.FilterSet):
        price = filters.AllLookupsFilter()

        # Not overridden by `AllLookupsFilter`
        price__gt = filters.NumberFilter(name='price', lookup_expr='gt', label='Minimum price')

        class Meta:
            model = Product

You cannot combine ``AllLookupsFilter`` with ``RelatedFilter`` as the filter names would clash.

.. code-block:: python

    class ProductFilter(filters.FilterSet):
        manufacturer = filters.RelatedFilter('ManufacturerFilter', queryset=Manufacturer.objects.all())
        manufacturer = filters.AllLookupsFilter()

To work around this, you have the following options:

.. code-block:: python

    class ProductFilter(filters.FilterSet):
        manufacturer = filters.RelatedFilter('ManufacturerFilter', queryset=Manufacturer.objects.all())

        class Meta:
            model = Product
            fields = {
                'manufacturer': '__all__',
            }

    # or

    class ProductFilter(filters.FilterSet):
        manufacturer = filters.RelatedFilter('ManufacturerFilter', queryset=Manufacturer.objects.all(), lookups='__all__')  # `lookups` also accepts a list

        class Meta:
            model = Product


Can I mix and match ``django-filter`` and ``django-rest-framework-filters``?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes you can. ``django-rest-framework-filters`` is simply an extension of ``django-filter``. Note
that ``RelatedFilter`` and other ``django-rest-framework-filters`` features are designed to work
with ``rest_framework_filters.FilterSet`` and will not function on a ``django_filters.FilterSet``.
However, the target ``RelatedFilter.filterset`` may point to a ``FilterSet`` from either package
and ``FilterSet``s from either package are compatible with the other's DRF backend.

.. code-block:: python

    # valid
    class VanillaFilter(django_filters.FilterSet):
        ...

    class DRFFilter(rest_framework_filters.FilterSet):
        vanilla = rest_framework_filters.RelatedFilter(filterset=VanillaFilter, queryset=...)


    # invalid
    class DRFFilter(rest_framework_filters.FilterSet):
        ...

    class VanillaFilter(django_filters.FilterSet):
        drf = rest_framework_filters.RelatedFilter(filterset=DRFFilter, queryset=...)


Caveats & Limitations
~~~~~~~~~~~~~~~~~~~~~

``MultiWidget`` is incompatible
"""""""""""""""""""""""""""""""

djangorestframework-filters is not compatible with form widgets that parse query names that differ from the filter's
attribute name. Although this only practically applies to ``MultiWidget``, it is a general limitation that affects
custom widgets that also have this behavior. Affected filters include ``RangeFilter``, ``DateTimeFromToRangeFilter``,
``DateFromToRangeFilter``, ``TimeRangeFilter``, and ``NumericRangeFilter``.

To demonstrate the incompatiblity, take the following filterset:

.. code-block:: python

    class PostFilter(FilterSet):
        publish_date = filters.DateFromToRangeFilter()

The above filter allows users to perform a ``range`` query on the publication date. The filter class internally uses
``MultiWidget`` to separately parse the upper and lower bound values. The incompatibility lies in that ``MultiWidget``
appends an index to its inner widget names. Instead of parsing ``publish_date``, it expects ``publish_date_0`` and
``publish_date_1``. It is possible to fix this by including the attribute name in the querystring, although this is
not recommended.

.. code-block::

    ?publish_date_0=2016-01-01&publish_date_1=2016-02-01&publish_date=

``MultiWidget`` is also discouraged since:

* ``core-api`` field introspection fails for similar reasons
* ``_0`` and ``_1`` are less API-friendly than ``_min`` and ``_max``

The recommended solutions are to either:

* Create separate filters for each of the sub-widgets (such as ``publish_date_min`` and ``publish_date_max``).
* Use a CSV-based filter such as those derived from ``BaseCSVFilter``/``BaseInFilter``/``BaseRangeFilter``. eg,

.. code-block::

    ?publish_date__range=2016-01-01,2016-02-01


Migrating to 1.0
----------------

``RelatedFilter.queryset`` now required
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The related filterset's model is no longer used to provide the default value for ``RelatedFilter.queryset``. This
change reduces the chance of unintentionally exposing data in the rendered filter forms. You must now explicitly
provide the ``queryset`` argument, or override the ``get_queryset()`` method (see `queryset callables`_).


``get_filters()`` renamed to ``expand_filters()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

django-filter has add a ``get_filters()`` classmethod to it's API, so this method has been renamed.

License
-------
Copyright (c) 2013-2015 Philip Neustrom <philipn@gmail.com>,
2016-2017 Ryan P Kilby <rpkilby@ncsu.edu>

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
