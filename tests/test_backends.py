
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework_filters import FilterSet

from .testapp import models, views

factory = APIRequestFactory()


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

        # Ensure that the filter_fields aren't altered
        self.assertDictEqual(views.FilterFieldsUserViewSet.filter_fields, {'username': '__all__'})

        response = self.client.get('/ff-users/', {'username': 'user1'}, content_type='json')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')
        self.assertDictEqual(views.FilterFieldsUserViewSet.filter_fields, {'username': '__all__'})

        response = self.client.get('/ff-users/', {'username': 'user1'}, content_type='json')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')
        self.assertDictEqual(views.FilterFieldsUserViewSet.filter_fields, {'username': '__all__'})

    def test_backend_output_sanity(self):
        """
        Sanity check to ensure backend can at least render something without crashing.
        """
        class SimpleViewSet(views.FilterFieldsUserViewSet):
            filter_fields = ['username']

        view = SimpleViewSet(action_map={})
        backend = view.filter_backends[0]
        request = view.initialize_request(factory.get('/'))
        html = backend().to_html(request, view.get_queryset(), view)

        self.assertHTMLEqual(html, """
        <h2>Field filters</h2>
        <form class="form" action="" method="get">
            <p>
                <label for="id_username">Username:</label>
                <input id="id_username" name="username" type="text" />
            </p>
            <button type="submit" class="btn btn-primary">Submit</button>
        </form>
        """)

    def test_request_obj_is_passed(test):
        """
        Ensure that the request object is passed from the backend to the filterset.
        See: https://github.com/philipn/django-rest-framework-filters/issues/149
        """
        class RequestCheck(FilterSet):
            def __init__(self, *args, **kwargs):
                super(RequestCheck, self).__init__(*args, **kwargs)
                test.assertIsNotNone(self.request)

            class Meta:
                model = models.User
                fields = ['username']

        class ViewSet(views.FilterFieldsUserViewSet):
            filter_class = RequestCheck

        view = ViewSet(action_map={})
        backend = view.filter_backends[0]
        request = view.initialize_request(factory.get('/'))
        backend().filter_queryset(request, view.get_queryset(), view)

    def test_exclusion(self):
        class RequestCheck(FilterSet):
            class Meta:
                model = models.User
                fields = ['username']

        class ViewSet(views.FilterFieldsUserViewSet):
            filter_class = RequestCheck

        view = ViewSet(action_map={})
        backend = view.filter_backends[0]
        request = view.initialize_request(factory.get('/?username=user1'))
        qs = backend().filter_queryset(request, view.get_queryset(), view)
        self.assertEqual([u.pk for u in qs], [1])

        request = view.initialize_request(factory.get('/?username!=user1'))
        qs = backend().filter_queryset(request, view.get_queryset(), view)
        self.assertEqual([u.pk for u in qs], [2])
