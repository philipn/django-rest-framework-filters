
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
