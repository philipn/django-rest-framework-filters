from django.test import TestCase

from rest_framework_filters import FilterSet, filters


class A(FilterSet):
    c = filters.RelatedFilter('tests.test_filters.C')


class B(FilterSet):
    a = filters.RelatedFilter('A')


class C(FilterSet):
    b = filters.RelatedFilter(B)


class RelatedFilterFiltersetTests(TestCase):
    # Test all three argument styles, but mainly ensure:
    # - `.filterset` is importable before parent FilterSet init
    # - Relative `.filterset` imports are durable to inheritance

    def subclass(self, cls):
        return type('Subclass%s' % cls.__name__, (cls, ), {})

    def test_filterset_absolute_import(self):
        for cls in [A, self.subclass(A)]:
            with self.subTest(cls=cls):
                self.assertIs(cls.base_filters['c'].filterset, C)

    def test_filterset_relative_import(self):
        for cls in [B, self.subclass(B)]:
            with self.subTest(cls=cls):
                self.assertIs(cls.base_filters['a'].filterset, A)

    def test_filterset_class(self):
        for cls in [C, self.subclass(C)]:
            with self.subTest(cls=cls):
                self.assertIs(cls.base_filters['b'].filterset, B)
