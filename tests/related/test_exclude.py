from django.test import TestCase

from tests.testapp.filters import BlogFilter
from tests.testapp.models import Blog, Post

from .data import RelationshipData


class ExcludeTests(RelationshipData, TestCase):
    """
    Test assumptions for excluding data across a to-many relationship.

    Given: GET /blogs?post__title__contains!=Lennon&post__publish_date__year!=2008
    Find: All blogs that *do not* have articles published in 2008 about Lennon

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

    # match blogs where *no* entry matches *all* of the factors (not A)
    CORRECT = [2, 3, 4, 8, 9, 10, 14]

    # match blogs where *no* entry matches *any* of the factors (not A, not B, not C)
    NOT_CORRECT_ANY = [4]

    # match blogs where *an* entry matches *none* of the factors (D)
    NOT_CORRECT_ONE = [4, 7, 9, 10, 12, 13, 14, 15]

    def test_single_exclude(self):
        # Verify that exclusion is not equivalent

        # q1 should be equivalent to q2/q4 and *not* q3/q5
        q1 = Blog.objects.exclude(post__title__contains='Lennon')

        # nested join
        q2 = Blog.objects.exclude(post__in=Post.objects.filter(title__contains='Lennon'))
        q3 = Blog.objects.filter(post__in=Post.objects.exclude(title__contains='Lennon'))

        # nested subquery
        q4 = Blog.objects.exclude(pk__in=Post.objects
                                             .filter(title__contains='Lennon')
                                             .values('blog'))
        q5 = Blog.objects.filter(pk__in=Post.objects
                                            .exclude(title__contains='Lennon')
                                            .values('blog'))

        # C, D, CD *all* entries do not have a title containing 'Lennon'
        self.verify(q1, [3, 4, 10])
        self.verify(q2, [3, 4, 10])
        self.verify(q4, [3, 4, 10])

        # These have *an* post where the title does not contain 'Lennon'
        self.verify(q3.distinct(), [3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
        self.verify(q5.distinct(), [3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])

    def test_chained_join_statements(self):
        q1 = Blog.objects \
                 .exclude(post__title__contains='Lennon') \
                 .exclude(post__publish_date__year=2008)

        self.verify(q1, self.NOT_CORRECT_ANY)

    def test_nested_join_outer_exclude(self):
        q2 = Blog.objects.exclude(
            post__in=Post.objects
                         .filter(title__contains='Lennon')
                         .filter(publish_date__year=2008),
        )

        self.verify(q2, self.CORRECT)

    def test_nested_join_inner_exclude(self):
        q3 = Blog.objects.filter(
            post__in=Post.objects
                         .exclude(title__contains='Lennon')
                         .exclude(publish_date__year=2008),
        )

        self.verify(q3, self.NOT_CORRECT_ONE)

    def test_nested_subquery_outer_exclude(self):
        q4 = Blog.objects.exclude(
            pk__in=Post.objects
                       .filter(title__contains='Lennon')
                       .filter(publish_date__year=2008)
                       .values('blog'),
        )

        self.verify(q4, self.CORRECT)

    def test_nested_subquery_inner_exclude(self):
        q5 = Blog.objects.filter(
            pk__in=Post.objects
                       .exclude(title__contains='Lennon')
                       .exclude(publish_date__year=2008)
                       .values('blog'),
        )

        self.verify(q5, self.NOT_CORRECT_ONE)

    # Test behavior
    def test_reverse_fk(self):
        GET = {
            'post__title__contains!': 'Lennon',
            'post__publish_date__year!': '2008',
        }
        self.verify(BlogFilter(GET).qs, self.NOT_CORRECT_ONE)
