from __future__ import print_function

import argparse
from timeit import timeit

from django.test import TestCase, Client, override_settings


parser = argparse.ArgumentParser()
parser.add_argument(
    '-v', '--verbosity', action='store', dest='verbosity', default=1,
    type=int, choices=[0, 1, 2, 3],
)
args, _ = parser.parse_known_args()


@override_settings(ROOT_URLCONF='tests.perf.urls')
class PerformanceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.iterations = range(1000)
        cls.threshold = 1.3

    def test_sanity(self):
        # sanity check to ensure our request are behaving as expected
        response = self.client.get('/df-notes/', {'author__username': 'bob'})
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/drf-notes/', {'author__username': 'bob'})
        self.assertEqual(response.status_code, 200)

    def test_response_time(self):
        data = {'author__username': 'bob'}

        df_time = timeit(lambda: self.client.get('/df-notes/', data), number=1000)
        drf_time = timeit(lambda: self.client.get('/drf-notes/', data), number=1000)

        if args.verbosity >= 2:
            print('\n' + '-' * 32)
            print('Response time performance')
            print('django-filter time:\t%.4fs' % df_time)
            print('drf-filters time:\t%.4fs' % drf_time)
            print('-' * 32)

        self.assertTrue(drf_time < (df_time * self.threshold))
