from urllib.parse import quote, urlencode

from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from rest_framework_filters import FilterSet

from .testapp import models, views

factory = APIRequestFactory()


class BackendTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        models.User.objects.create(username="user1", email="user1@example.org")
        models.User.objects.create(username="user2", email="user2@example.org")

    def test_django_filter_compatibility(self):
        response = self.client.get('/df-users/', {'username': 'user1'}, content_type='json')

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')

    def test_filterset_fields_reusability(self):
        # Ensure auto-generated FilterSet is reusable w/ filterset_fields. See:
        # https://github.com/philipn/django-rest-framework-filters/issues/81

        # Ensure that the filterset_fields aren't altered
        self.assertDictEqual(views.FilterFieldsUserViewSet.filterset_fields, {'username': '__all__'})

        response = self.client.get('/ff-users/', {'username': 'user1'}, content_type='json')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')
        self.assertDictEqual(views.FilterFieldsUserViewSet.filterset_fields, {'username': '__all__'})

        response = self.client.get('/ff-users/', {'username': 'user1'}, content_type='json')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')
        self.assertDictEqual(views.FilterFieldsUserViewSet.filterset_fields, {'username': '__all__'})

    def test_request_obj_is_passed(test):
        """
        Ensure that the request object is passed from the backend to the filterset.
        See: https://github.com/philipn/django-rest-framework-filters/issues/149
        """
        called = False

        class RequestCheck(FilterSet):
            def __init__(self, *args, **kwargs):
                super(RequestCheck, self).__init__(*args, **kwargs)
                test.assertIsNotNone(self.request)

                nonlocal called
                called = True

            class Meta:
                model = models.User
                fields = ['username']

        class ViewSet(views.FilterFieldsUserViewSet):
            filterset_class = RequestCheck

        view = ViewSet(action_map={})
        backend = view.filter_backends[0]
        request = view.initialize_request(factory.get('/'))
        backend().filter_queryset(request, view.get_queryset(), view)
        test.assertTrue(called)

    def test_exclusion(self):
        class RequestCheck(FilterSet):
            class Meta:
                model = models.User
                fields = ['username']

        class ViewSet(views.FilterFieldsUserViewSet):
            filterset_class = RequestCheck

        view = ViewSet(action_map={})
        backend = view.filter_backends[0]
        request = view.initialize_request(factory.get('/?username=user1'))
        qs = backend().filter_queryset(request, view.get_queryset(), view)
        self.assertEqual([u.pk for u in qs], [1])

        request = view.initialize_request(factory.get('/?username!=user1'))
        qs = backend().filter_queryset(request, view.get_queryset(), view)
        self.assertEqual([u.pk for u in qs], [2])


class BackendRenderingTests(APITestCase):

    def render(self, viewset_class, data=None):
        url = '/' if not data else '/?' + urlencode(data, True)
        view = viewset_class(action_map={})
        backend = view.filter_backends[0]
        request = view.initialize_request(factory.get(url))
        return backend().to_html(request, view.get_queryset(), view)

    def test_sanity(self):
        # Sanity check to ensure backend can render without crashing.
        class SimpleViewSet(views.FilterFieldsUserViewSet):
            filterset_fields = ['username', ]

        self.assertHTMLEqual(self.render(SimpleViewSet), """
        <h2>Field filters</h2>
        <form class="form" action="" method="get">
            <p>
                <label for="id_username">Username:</label>
                <input id="id_username" name="username" type="text" />
            </p>
            <button type="submit" class="btn btn-primary">Submit</button>
        </form>
        """)

    def test_rendering_doesnt_affect_filterset_class(self):
        class SimpleFilterSet(FilterSet):
            class Meta:
                model = models.User
                fields = ['username', 'email']

        class SimpleViewSet(views.FilterFieldsUserViewSet):
            filterset_class = SimpleFilterSet

        self.assertEqual(list(SimpleFilterSet({'username!': ''}).form.fields), ['username!'])
        self.render(SimpleViewSet)
        self.assertEqual(list(SimpleFilterSet({'username!': ''}).form.fields), ['username!'])


class ComplexFilterBackendTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        models.User.objects.create(username="user1", email="user1@example.com")
        models.User.objects.create(username="user2", email="user2@example.com")
        models.User.objects.create(username="user3", email="user3@example.org")
        models.User.objects.create(username="user4", email="user4@example.org")

    def test_valid(self):
        readable = '(username%3Duser1)|(email__contains%3Dexample.org)'
        response = self.client.get('/ffcomplex-users/?filters=' + quote(readable), content_type='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            [r['username'] for r in response.data],
            ['user1', 'user3', 'user4']
        )

    def test_invalid(self):
        readable = '(username%3Duser1)asdf(email__contains%3Dexample.org)'
        response = self.client.get('/ffcomplex-users/?filters=' + quote(readable), content_type='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.data, {
            'filters': ["Invalid querystring operator. Matched: 'asdf'."],
        })

    def test_invalid_filterset_errors(self):
        readable = '(id%3Dfoo) | (id%3Dbar)'
        response = self.client.get('/ffcomplex-users/?filters=' + quote(readable), content_type='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.data, {
            'filters': {
                'id=foo': {
                    'id': ['Enter a number.'],
                },
                'id=bar': {
                    'id': ['Enter a number.'],
                },
            },
        })

    def test_pagination_compatibility(self):
        """
        Ensure that complex-filtering does not interfere with additional query param processing.
        """
        readable = '(email__contains%3Dexample.org)'

        # sanity check w/o pagination
        response = self.client.get('/ffcomplex-users/?filters=' + quote(readable), content_type='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            [r['username'] for r in response.data],
            ['user3', 'user4']
        )

        # sanity check w/o complex-filtering
        response = self.client.get('/ffcomplex-users/?page_size=1', content_type='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertListEqual(
            [r['username'] for r in response.data['results']],
            ['user1']
        )

        # pagination + complex-filtering
        response = self.client.get('/ffcomplex-users/?page_size=1&filters=' + quote(readable), content_type='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertListEqual(
            [r['username'] for r in response.data['results']],
            ['user3']
        )
