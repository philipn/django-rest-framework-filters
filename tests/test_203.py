from rest_framework.test import APITestCase, APIRequestFactory

factory = APIRequestFactory()


class Issue203Tests(APITestCase):

    def test_releases(self):
        self.client.get('/releases/', content_type='json')

    def test_applications(self):
        self.client.get('/applications/', content_type='json')
