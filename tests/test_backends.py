
from rest_framework.test import APITestCase

from .testapp import models


class BackendTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        models.User.objects.create(username="user1", email="user1@example.org")
        models.User.objects.create(username="user2", email="user2@example.org")

    def test_django_filter_compatibility(self):
        response = self.client.get('/df-users/', {'username': 'user1'}, content_type='json')

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')

    def test_filter_fields_reusability(self):
        # Ensure auto-generated FilterSet is reusable w/ filter_fields. See:
        # https://github.com/philipn/django-rest-framework-filters/issues/81
        response = self.client.get('/ff-users/', {'username': 'user1'}, content_type='json')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')

        response = self.client.get('/ff-users/', {'username': 'user1'}, content_type='json')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')
