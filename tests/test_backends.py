
from django.test import TestCase, Client


class BackendTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get(self):
        self.client.get('/notes')
