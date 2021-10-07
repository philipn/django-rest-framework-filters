import argparse
from timeit import repeat

from django.test import TestCase, override_settings, tag
from rest_framework.test import APIRequestFactory

from tests.perf import views
from tests.testapp import models

factory = APIRequestFactory()


# parse command verbosity level & use for results output
parser = argparse.ArgumentParser()
parser.add_argument(
    '-v', '--verbosity', action='store', dest='verbosity', default=1,
    type=int, choices=[0, 1, 2, 3],
)
args, _ = parser.parse_known_args()
verbosity = args.verbosity


@tag('perf')
class PerfTestMixin(object):
    # This mixin provides common setup for testing the performance differences between
    # django-filter and django-rest-framework-filters. A callable for each implementation
    # should be generated that will return semantically equivalent results.
    iterations = 1000
    repeat = 5
    threshold = 1.0
    label = None

    @classmethod
    def setUpTestData(cls):
        bob = models.User.objects.create(username='bob')
        joe = models.User.objects.create(username='joe')

        models.Note.objects.create(author=bob, title='Note 1')
        models.Note.objects.create(author=bob, title='Note 2')
        models.Note.objects.create(author=joe, title='Note 3')
        models.Note.objects.create(author=joe, title='Note 4')

    def get_callable(self, *args):
        # Returns the callable and callable's *args to be used for each test
        # iteration. The performance of the callable is what is under test.
        raise NotImplementedError

    def django_filter_args(self):
        # Arguments passed to `get_callable()` in order to create
        # django-filter test iterations.
        raise NotImplementedError

    def rest_framework_filters_args(self):
        # Arguments passed to `get_callable()` in order to create
        # django-rest-framework-filters test iterations.
        raise NotImplementedError

    def validate_result(self, result):
        # Provides the validation logic that the sanity test uses to check its test
        # call results against.

        # Since the calls for both implementations must be comparable or at least
        # semantically equivalent, this method should validate both results.
        raise NotImplementedError

    def test_sanity(self):
        # sanity check to ensure the call results are valid
        call, args = self.get_callable(*self.django_filter_args())
        self.validate_result(call(*args))

        call, args = self.get_callable(*self.rest_framework_filters_args())
        self.validate_result(call(*args))

    def test_performance(self):
        call, args = self.get_callable(*self.django_filter_args())
        df_time = min(repeat(
            lambda: call(*args),
            number=self.iterations,
            repeat=self.repeat,
        ))

        call, args = self.get_callable(*self.rest_framework_filters_args())
        drf_time = min(repeat(
            lambda: call(*args),
            number=self.iterations,
            repeat=self.repeat,
        ))

        diff = (drf_time - df_time) / df_time * 100.0

        if verbosity >= 2:
            print('\n' + '-' * 32)
            print('%s performance' % self.label)
            print('django-filter time:\t%.4fs' % df_time)
            print('drf-filters time:\t%.4fs' % drf_time)
            print('performance diff:\t%+.2f%% ' % diff)
            print('-' * 32)

        self.assertLess(drf_time, df_time * self.threshold)


class FilterBackendTests(PerfTestMixin, TestCase):
    # How much faster or slower is drf-filters than django-filter?
    threshold = 1.5
    label = 'Filter Backend'

    def get_callable(self, view_class):
        view = view_class(action_map={'get': 'list'})
        data = {'author__username': 'bob', 'title__contains': 'Note'}
        request = factory.get('/', data=data)
        request = view.initialize_request(request)
        backend = view.filter_backends[0]

        call = backend().filter_queryset
        args = [
            request, view.get_queryset(), view,
        ]

        return call, args

    def django_filter_args(self):
        return [views.DFNoteViewSet]

    def rest_framework_filters_args(self):
        return [views.DRFFNoteViewSet]

    def validate_result(self, qs):
        self.assertEqual(qs.count(), 2)


@override_settings(ROOT_URLCONF='tests.perf.urls')
class WSGIResponseTests(PerfTestMixin, TestCase):
    # How much does drf-filters affect the request/response cycle? This includes
    # response rendering, which provides a more practical picture of the performance
    # costs of using drf-filters.
    threshold = 1.3
    label = 'WSGI Response'

    def get_callable(self, url):
        call = self.client.get
        args = [
            url, {'author__username': 'bob', 'title__contains': 'Note'},
        ]

        return call, args

    def django_filter_args(self):
        return ['/df-notes/']

    def rest_framework_filters_args(self):
        return ['/drf-notes/']

    def validate_result(self, response):
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 2)
