
## Performance Testing

The included tests are an initial pass at guaging the performance of filtering across
relationships via `RelatedFilter`. The intent is to provide some assurance that:

- the package does not perform glaringly worse than pure django-filter.
- new changes do no inadvertantly decrease performance.


### Running the tests

The performance tests have been isolated from the main test suite so that they can be
ran independently. Simply run:

    $ tox -e performance

Or more directly:

    $ python manage.py test tests.perf


### Notes:

Although the performance tests are relatively quick, they will occasionally fail in CI
due to fluctuations in VM performance. The easiest way to reduce the number of random
failures is to simply run the performance tests in a single, separate build.
