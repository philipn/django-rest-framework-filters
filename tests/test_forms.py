from django import forms
from django.test import TestCase

from rest_framework_filters import FilterSet, filters

from .testapp.filters import PostFilter
from .testapp.models import Post, User


class FilterSetFormTests(TestCase):

    def test_form_inheritance(self):
        class MyForm(forms.Form):
            pass

        class F(FilterSet):
            class Meta:
                model = Post
                fields = []
                form = MyForm

        self.assertIsInstance(F().form, MyForm)

    def test_subset_disabled_form_fields(self):
        # Form fields should reliably display when the subset is disabled
        class F(FilterSet):
            class Meta:
                model = Post
                fields = ['title', 'content']

        F = F.disable_subset()
        form = F({}).form
        self.assertEqual(list(form.fields), ['title', 'content'])

    def test_unbound_form_fields(self):
        class F(FilterSet):
            class Meta:
                model = Post
                fields = ['title', 'content']

        form = F().form
        self.assertEqual(list(form.fields), [])

    def test_bound_form_fields(self):
        class F(FilterSet):
            class Meta:
                model = Post
                fields = ['title', 'content']

        form = F({}).form
        self.assertEqual(list(form.fields), [])

        form = F({'title': 'foo'}).form
        self.assertEqual(list(form.fields), ['title'])

    def test_related_form_fields(self):
        # FilterSet form should not contain fields from related filtersets

        class F(FilterSet):
            author = filters.RelatedFilter(
                'tests.testapp.filters.UserFilter',
                queryset=User.objects.all(),
            )

            class Meta:
                model = Post
                fields = ['title', 'author']

        f = F({'title': '', 'author': '', 'author__email': ''})
        form = f.form
        self.assertEqual(list(form.fields), ['title', 'author'])

        form = f.related_filtersets['author'].form
        self.assertEqual(list(form.fields), ['email'])

    def test_validation_errors(self):
        f = PostFilter({
            'publish_date__year': 'foo',
            'author__last_login__date': 'bar',
        })
        self.assertEqual(f.form.errors, {
            'publish_date__year': ['Enter a number.'],
            'author__last_login__date': ['Enter a valid date.'],
        })
