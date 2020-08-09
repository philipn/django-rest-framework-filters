from urllib.parse import quote, urlencode

import django_filters
from django.test import modify_settings
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from rest_framework_filters import FilterSet, filters
from rest_framework_filters.backends import RestFrameworkFilterBackend
from rest_framework_filters.filterset import SubsetDisabledMixin

from .testapp import models, views

factory = APIRequestFactory()


class RenderMixin:

    def render(self, viewset_class, data=None):
        url = '/' if not data else '/?' + urlencode(data, True)
        view = viewset_class(action_map={})
        backend = view.filter_backends[0]
        request = view.initialize_request(factory.get(url))
        return backend().to_html(request, view.get_queryset(), view)


class BackendTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        models.User.objects.create(username="user1", email="user1@example.org")
        models.User.objects.create(username="user2", email="user2@example.org")

    def test_django_filter_compatibility(self):
        response = self.client.get('/df-users/', {'username': 'user1'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')

    def test_filterset_fields_reusability(self):
        # Ensure auto-generated FilterSet is reusable w/ filterset_fields. See:
        # https://github.com/philipn/django-rest-framework-filters/issues/81

        # Ensure that the filterset_fields aren't altered
        self.assertDictEqual(
            views.FilterFieldsUserViewSet.filterset_fields,
            {'username': '__all__'},
        )

        response = self.client.get('/ff-users/', {'username': 'user1'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')
        self.assertDictEqual(
            views.FilterFieldsUserViewSet.filterset_fields,
            {'username': '__all__'},
        )

        response = self.client.get('/ff-users/', {'username': 'user1'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')
        self.assertDictEqual(
            views.FilterFieldsUserViewSet.filterset_fields,
            {'username': '__all__'},
        )

    def test_request_obj_is_passed(test):
        # Ensure that the request object is passed from the backend to the filterset.
        # See: https://github.com/philipn/django-rest-framework-filters/issues/149
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

    def test_disabled(self):
        # Views with no `filterset_class` or `filterset_fields` should not
        # error when used with the RestFrameworkFilterBackend.
        # see: https://github.com/philipn/django-rest-framework-filters/issues/230
        view = views.UnfilteredUserViewSet(action_map={})
        backend = view.filter_backends[0]
        request = view.initialize_request(factory.get('/'))

        # ensure view has backend and is missing attributes
        self.assertIs(backend, RestFrameworkFilterBackend)
        self.assertFalse(hasattr(view, 'filterset_class'))
        self.assertFalse(hasattr(view, 'filterset_fields'))

        # filterset should be None, method should not error
        self.assertIsNone(backend().get_filterset(request, view.queryset, view))

        # patched method should not error
        backend = backend()
        with backend.patch_for_rendering(request):
            self.assertIsNone(backend.get_filterset(request, view.queryset, view))


class BackendRenderingTests(RenderMixin, APITestCase):

    def test_sanity(self):
        # Sanity check to ensure backend can render without crashing.
        class SimpleViewSet(views.FilterFieldsUserViewSet):
            filterset_fields = ['username']

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

    def test_django_filter_filterset_compatibility(self):
        class SimpleFilterSet(django_filters.FilterSet):
            class Meta:
                model = models.User
                fields = ['username']

        class SimpleViewSet(views.FilterFieldsUserViewSet):
            filterset_class = SimpleFilterSet

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

    def test_related_filterset(self):
        class UserFilter(FilterSet):
            username = filters.CharFilter()

        class NoteFilter(FilterSet):
            author = filters.RelatedFilter(
                filterset=UserFilter,
                queryset=models.User.objects.all(),
                label='Writer',
            )

        class RelatedViewSet(views.NoteViewSet):
            filterset_class = NoteFilter

        self.assertHTMLEqual(self.render(RelatedViewSet), """
        <h2>Field filters</h2>
        <form class="form" action="" method="get">
            <p>
                <label for="id_author">Writer:</label>
                <select id="id_author" name="author">
                    <option selected value="">---------</option>
                </select>
            </p>


            <fieldset>
                <legend>Writer</legend>
                <p>
                    <label for="id_author__username">Username:</label>
                    <input id="id_author__username" name="author__username" type="text" />
                </p>
            </fieldset>

            <button type="submit" class="btn btn-primary">Submit</button>
        </form>
        """)

    def test_related_filterset_validation(self):
        class UserFilter(FilterSet):
            last_login = filters.DateFilter()

        class NoteFilter(FilterSet):
            author = filters.RelatedFilter(
                filterset=UserFilter,
                queryset=models.User.objects.all(),
                label='Writer',
            )

        class RelatedViewSet(views.NoteViewSet):
            filterset_class = NoteFilter

        context = {'author': 'invalid', 'author__last_login': 'invalid'}
        self.assertHTMLEqual(self.render(RelatedViewSet, context), """
        <h2>Field filters</h2>
        <form class="form" action="" method="get">
            <ul class="errorlist">
                <li>
                    Select a valid choice. That choice
                    is not one of the available choices.
                </li>
            </ul>
            <p>
                <label for="id_author">Writer:</label>
                <select id="id_author" name="author">
                    <option value="">---------</option>
                </select>
            </p>


            <fieldset>
                <legend>Writer</legend>

                <ul class="errorlist">
                    <li>Enter a valid date.</li>
                </ul>
                <p>
                    <label for="id_author__last_login">Last login:</label>
                    <input id="id_author__last_login"
                           name="author__last_login"
                           type="text"
                           value="invalid" />
                </p>
            </fieldset>

            <button type="submit" class="btn btn-primary">Submit</button>
        </form>
        """)

    def test_rendering_doesnt_affect_filterset_classes(self):
        class NoteFilter(FilterSet):
            title = filters.CharFilter()

        class UserFilter(FilterSet):
            notes = filters.RelatedFilter(
                field_name='note',
                filterset=NoteFilter,
                queryset=models.Note.objects.all(),
            )

        class SimpleViewSet(views.FilterFieldsUserViewSet):
            filterset_class = UserFilter

        self.render(SimpleViewSet)

        # check that ViewSet filterset_class isn't modified
        filterset = SimpleViewSet.filterset_class
        self.assertTrue(issubclass(filterset, FilterSet))
        self.assertFalse(issubclass(filterset, SubsetDisabledMixin))

        # check that FilterSet.related_filters aren't modified
        filterset = UserFilter.base_filters['notes'].filterset
        self.assertTrue(issubclass(filterset, FilterSet))
        self.assertFalse(issubclass(filterset, SubsetDisabledMixin))

    def test_patch_for_rendering(self):
        class NoteFilter(FilterSet):
            title = filters.CharFilter()

        class UserFilter(FilterSet):
            notes = filters.RelatedFilter(
                field_name='note',
                filterset=NoteFilter,
                queryset=models.Note.objects.all(),
            )

        class SimpleViewSet(views.FilterClassUserViewSet):
            filterset_class = UserFilter

        view = SimpleViewSet(action_map={})
        request = view.initialize_request(factory.get('/'))
        backend = view.filter_backends[0]
        backend = backend()

        original = backend.get_filterset_class
        with backend.patch_for_rendering(request):
            filterset = backend.get_filterset(request, view.get_queryset(), view)

        # check ViewSet filterset
        self.assertIsInstance(filterset, FilterSet)
        self.assertIsInstance(filterset, SubsetDisabledMixin)

        # check related filtersets
        filterset = filterset.related_filtersets['notes']
        self.assertIsInstance(filterset, FilterSet)
        self.assertIsInstance(filterset, SubsetDisabledMixin)

        # ensure original method was reset
        self.assertEqual(backend.get_filterset_class, original)

    def test_patch_for_rendering_handles_exception(self):
        view = views.FilterClassUserViewSet(action_map={})
        request = view.initialize_request(factory.get('/'))
        backend = view.filter_backends[0]
        backend = backend()

        original = backend.get_filterset_class
        with self.assertRaises(Exception):
            with backend.patch_for_rendering(request):
                raise Exception

        # ensure original method was reset
        self.assertEqual(backend.get_filterset_class, original)


@modify_settings(INSTALLED_APPS={'append': ['crispy_forms']})
class BackendCrispyFormsRenderingTests(RenderMixin, APITestCase):

    def test_crispy_forms_filterset_compatibility(self):
        class SimpleCrispyFilterSet(FilterSet):
            class Meta:
                model = models.User
                fields = ['username']

        class SimpleViewSet(views.FilterFieldsUserViewSet):
            filterset_class = SimpleCrispyFilterSet

        self.assertHTMLEqual(self.render(SimpleViewSet), """
        <h2>Field filters</h2>
        <form method="get">
            <div id="div_id_username" class="form-group">
                <label for="id_username" class="control-label ">Username</label>
                <div class=" controls">
                    <input type="text"
                           name="username"
                           class="form-control textinput textInput"
                           id="id_username">
                </div>
            </div>
            <button type="submit" class="btn btn-primary">Submit</button>
        </form>
        """)

    def test_related_filterset_crispy_forms(self):
        class UserFilter(FilterSet):
            username = filters.CharFilter()

        class NoteFilter(FilterSet):
            author = filters.RelatedFilter(
                filterset=UserFilter,
                queryset=models.User.objects.all(),
                label='Writer',
            )

        class RelatedViewSet(views.NoteViewSet):
            filterset_class = NoteFilter

        self.assertHTMLEqual(self.render(RelatedViewSet), """
        <h2>Field filters</h2>
        <form method="get">
            <div id="div_id_author" class="form-group">
                <label for="id_author" class="control-label ">Writer</label>
                <div class=" controls">
                    <select name="author" class="select form-control" id="id_author">
                        <option value="" selected>---------</option>
                    </select>
                </div>
            </div>

            <fieldset>
                <legend>Writer</legend>

                <div id="div_id_author__username" class="form-group">
                    <label for="id_author__username" class="control-label ">
                        Username
                    </label>
                    <div class=" controls">
                        <input type="text" class="form-control textinput textInput"
                               id="id_author__username" name="author__username">
                    </div>
                </div>
            </fieldset>

            <button type="submit" class="btn btn-primary">Submit</button>
        </form>
        """)


class ComplexFilterBackendTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        models.User.objects.create(username="user1", email="user1@example.com")
        models.User.objects.create(username="user2", email="user2@example.com")
        models.User.objects.create(username="user3", email="user3@example.org")
        models.User.objects.create(username="user4", email="user4@example.org")

    def test_valid(self):
        readable = quote('(username%3Duser1)|(email__contains%3Dexample.org)')
        response = self.client.get('/ffcomplex-users/?filters=' + readable)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            [r['username'] for r in response.data],
            ['user1', 'user3', 'user4'],
        )

    def test_invalid(self):
        readable = quote('(username%3Duser1)asdf(email__contains%3Dexample.org)')
        response = self.client.get('/ffcomplex-users/?filters=' + readable)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.data, {
            'filters': ["Invalid querystring operator. Matched: 'asdf'."],
        })

    def test_invalid_filterset_errors(self):
        readable = quote('(id%3Dfoo) | (id%3Dbar)')
        response = self.client.get('/ffcomplex-users/?filters=' + readable)

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
        # Ensure that complex-filtering does not affect additional query param processing.
        readable = quote('(email__contains%3Dexample.org)')

        # sanity check w/o pagination
        response = self.client.get('/ffcomplex-users/?filters=' + readable)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            [r['username'] for r in response.data],
            ['user3', 'user4'],
        )

        # sanity check w/o complex-filtering
        response = self.client.get('/ffcomplex-users/?page_size=1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertListEqual(
            [r['username'] for r in response.data['results']],
            ['user1'],
        )

        # pagination + complex-filtering
        response = self.client.get('/ffcomplex-users/?page_size=1&filters=' + readable)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertListEqual(
            [r['username'] for r in response.data['results']],
            ['user3'],
        )
