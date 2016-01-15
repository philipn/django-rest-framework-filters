Unreleased:
-----------

* Adds support for Django 1.9
* #47 Changes implementation of MethodFilterss
* Drops support for Django 1.7
* #49 Fix ALL_LOOKUPS shortcut to obey filter overrides (in, isnull)
* #46 Fix boolean filter behavior (#25) and isnull override (#6)

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
* #35 Fix python 3.5 compatibility issue.
* Drops support for Django 1.6 and below

v0.4.0:
-------

* Adds support for Django 1.8, DRF 3.2
* Drops support for Python 2.6, DRF 2.x
* #23 Adds __in filtering for numeric field types. eg, ?id__in=1,2,3
