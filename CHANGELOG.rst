Unreleased:
-----------

* #242 Deprecate ``AllLookupsFilter``
* #191 Fix ``name`` => ``field_name`` warnings


v0.11.1:
--------

Fixes a packaging issue in v0.11.0


v0.11.0:
--------

This is a minor release that upgrades django-filter compatibility from ``v1.0``
to ``v1.1``. No new functionality has been introduced.


v0.10.2.post0:
--------------

* #253 Set django-filter version at 1.x-compatible releases.


v0.10.2:
--------

This is a maintenance release that fixes compatibility with django-filter.

* #189 Fix method name collision


v0.10.1:
--------

This is a maintenance release that fixes the following bugs:

* #172 Prevent deepcopying of filter's parent


v0.10.0:
--------

This release primarily adds compatibility with django-filter 1.0 (more details
in #144), and is an intermediate step to overhauling the behavior of filters
that span relationships.

As `RelatedFilter` is a subclass of `ModelChoiceFilter`, you may take advantage
of the `callable` behavior for the `queryset` argument. The `queryset` is now a
required argument, which is a forwards-incompatible change. You can provide the
model's default queryset to maintain the current behavior, or a callable, which
will allow you to filter the queryset by the request's properties.

* #124 Removed deprecation warnings
* #128 Fix all lookups handling for related fields
* #129 Fix template rendering
* #139 Fix metaclass inheritance bug
* #146 Make `RelatedFilter.queryset` a required argument
* #154 Add python 3.6 support
* #161 Fix request-based filtering
* #170 Improve RelatedFilter queryset error message

v0.9.1:
-------

* #128 Fix all lookups handling for related fields
* #129 Fix backend template rendering
* #148 Version lock django-filter<1.0 due to API incompatibilities

v0.9.0:
-------

This release is tied to the 0.15.0 update of django-filter, and is in preparation of
a (near) simultaneous 1.0 release. All current deprecations will be removed in the
next release.

* Updates django-filter requirement to 0.15.0
* #101 Add support for Django 1.10, set DRF support to 3.3, 3.4, and drop support for python 3.2
* #114 Add ``lookups`` argument to ``RelatedFilter``
* #113 Deprecated ``MethodFilter`` for new ``Filter.method`` argument
* #123 Fix declared filters being overwritten by ``AllLookupsFilter``

v0.8.1:
-------

* Fix bug where AllLookupsFilter would override a declared filter of the same name
* #84 Fix AllLookupsFilter compatibility with ``ForeignObject`` related fields
* #82 Fix AllLookupsFilter compatibility with mixin FilterSets
* #81 Fix bug where FilterSet modified ``ViewSet.filter_fields``
* #79 Prevent infinite recursion for chainable transforms, fixing compatiblity
  w/ ``django.contrib.postgres``

v0.8.0:
-------

This release is tied to a major update of django-filter (more details in #66),
which fixes how lookup expressions are resolved. 'in', 'range', and 'isnull'
lookups no longer require special handling by django-rest-framework-filters.
This has the following effects:

  * Deprecates ArrayDecimalField/InSetNumberFilter
  * Deprecates ArrayCharField/InSetCharFilter
  * Deprecates FilterSet.fix_filter_field
  * Deprecates ALL_LOOKUPS in favor of '__all__' constant
  * AllLookupsFilter now generates only valid lookup expressions

* #2 'range' lookup types do not work
* #15 Date lookup types do not work (year, day, ...)
* #16 'in' lookup types do not work
* #64 Fix browsable API filter form
* #69 Fix compatibility with base django-filter `FilterSet`s
* #70 Refactor related filter handling, fixing some edge cases
* Deprecated 'cache' argument to FilterSet
* #73 Warn use of `order_by`

v0.7.0:
-------

* #61 Change django-filter requirement to 0.12.0
* Adds support for Django 1.9
* #47 Changes implementation of MethodFilterss
* Drops support for Django 1.7
* #49 Fix ALL_LOOKUPS shortcut to obey filter overrides (in, isnull)
* #46 Fix boolean filter behavior (#25) and isnull override (#6)
* #60 Fix filtering on nonexistent related field

v0.6.0:
-------

* #43 Adds a filter exclusion/negation syntax. eg, ?some_filter!=some_value
* #44 Sets the minimum django-filter version required

v0.5.0:
-------

* #38 Rework of related filtering, improving performance (#8) and some minor correctness issues
* #35 Add ALL_LOOKUPS shortcut for dict-style filter definitions
* #31 Fix timezone-aware datetime handling
* #36 Fix '__in' filter to work with strings
* #33 Fix RelatedFilter handling to not override existing isnull filters
* #35 Fix python 3.5 compatibility issue
* Drops support for Django 1.6 and below

v0.4.0:
-------

* Adds support for Django 1.8, DRF 3.2
* Drops support for Python 2.6, DRF 2.x
* #23 Adds __in filtering for numeric field types. eg, ?id__in=1,2,3
