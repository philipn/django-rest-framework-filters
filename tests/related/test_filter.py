from django.test import TestCase

from tests.testapp.filters import BlogFilter
from tests.testapp.models import Blog, Post

from .data import RelationshipData


class FilterTests(RelationshipData, TestCase):
    """
    Test assumptions for filtering data across a to-many relationship.

    Given: GET /blogs?post__title__contains=Lennon&post__publish_date__year=2008
    Find: All blogs that have articles published in 2008 about Lennon

    Posts have two factors:
    - A: title__contains=Lennon
    - B: publish_date__year=2008

    There are four possible types of posts:
    - postA:  A   B
    - postB:  A  ~B
    - postC: ~A   B
    - postD: ~A  ~B

    Ther are 15 unique combinations of blogs using the above four posts:
    A, B, C, D, AB, AC, AD, BC, BD, CD, ABC, ABD, ACD, BCD, ABCD
    1, 2, 3, 4, 5,  6,  7,  8,  9,  10, 11,  12,  13,  14,  15
    """

    # match blogs where entries match all conditions (A)
    CORRECT = [1, 5, 6, 7, 11, 12, 13, 15]

    # match blogs where all of the conditions occur (A, B+C)
    NOT_CORRECT = [1, 5, 6, 7, 8, 11, 12, 13, 14, 15]

    def test_single_filter(self):
        # Verify that the following queries are equivalent
        q1 = Blog.objects.filter(post__title__contains='Lennon')
        q2 = Blog.objects.filter(post__in=Post.objects
                                              .filter(title__contains='Lennon'))
        q3 = Blog.objects.filter(pk__in=Post.objects
                                            .filter(title__contains='Lennon')
                                            .values('blog'))

        expected = [1, 2, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15]

        self.verify(q1.distinct(), expected)
        self.verify(q2.distinct(), expected)
        self.verify(q3, expected)

    def test_chained_join_statements(self):
        q1 = Blog.objects \
            .filter(post__title__contains='Lennon') \
            .filter(post__publish_date__year=2008)

        self.verify(q1.distinct(), self.NOT_CORRECT)

    def test_nested_join(self):
        q2 = Blog.objects.filter(
            post__in=Post.objects
                         .filter(title__contains='Lennon')
                         .filter(publish_date__year=2008),
        )

        self.verify(q2, self.CORRECT)

    def test_nested_subquery(self):
        q3 = Blog.objects.filter(
            pk__in=Post.objects
                       .filter(title__contains='Lennon')
                       .filter(publish_date__year=2008)
                       .values('blog'),
        )

        self.verify(q3, self.CORRECT)

    # Test behavior
    def test_reverse_fk(self):
        GET = {
            'post__title__contains': 'Lennon',
            'post__publish_date__year': '2008',
        }
        self.verify(BlogFilter(GET).qs, self.CORRECT)
