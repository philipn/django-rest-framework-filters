from operator import attrgetter

from ..testapp.models import Blog, Post


class RelationshipData:
    """
    Mixin for providing the data for the relationship tests.

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

    @classmethod
    def setUpTestData(cls):
        b = Blog.objects.create(pk=1, name='Blog A')
        cls.postA(b)

        b = Blog.objects.create(pk=2, name='Blog B')
        cls.postB(b)

        b = Blog.objects.create(pk=3, name='Blog C')
        cls.postC(b)

        b = Blog.objects.create(pk=4, name='Blog D')
        cls.postD(b)

        b = Blog.objects.create(pk=5, name='Blog AB')
        cls.postA(b), cls.postB(b)

        b = Blog.objects.create(pk=6, name='Blog AC')
        cls.postA(b), cls.postC(b)

        b = Blog.objects.create(pk=7, name='Blog AD')
        cls.postA(b), cls.postD(b)

        b = Blog.objects.create(pk=8, name='Blog BC')
        cls.postB(b), cls.postC(b)

        b = Blog.objects.create(pk=9, name='Blog BD')
        cls.postB(b), cls.postD(b)

        b = Blog.objects.create(pk=10, name='Blog CD')
        cls.postC(b), cls.postD(b)

        b = Blog.objects.create(pk=11, name='Blog ABC')
        cls.postA(b), cls.postB(b), cls.postC(b)

        b = Blog.objects.create(pk=12, name='Blog ABD')
        cls.postA(b), cls.postB(b), cls.postD(b)

        b = Blog.objects.create(pk=13, name='Blog ACD')
        cls.postA(b), cls.postC(b), cls.postD(b)

        b = Blog.objects.create(pk=14, name='Blog BCD')
        cls.postB(b), cls.postC(b), cls.postD(b)

        b = Blog.objects.create(pk=15, name='Blog ABCD')
        cls.postA(b), cls.postB(b), cls.postC(b), cls.postD(b)

    @classmethod
    def postA(cls, blog):
        Post.objects.create(
            blog=blog,
            title='Something about Lennon',
            publish_date='2008-01-01',
        )

    @classmethod
    def postB(cls, blog):
        Post.objects.create(
            blog=blog,
            title='Something about Lennon',
            publish_date='2010-01-01',
        )

    @classmethod
    def postC(cls, blog):
        Post.objects.create(
            blog=blog,
            title='Ringo was a Starr',
            publish_date='2008-01-01',
        )

    @classmethod
    def postD(cls, blog):
        Post.objects.create(
            blog=blog,
            title='Ringo was a Starr',
            publish_date='2010-01-01',
        )

    def verify(self, qs, expected):
        self.assertQuerysetEqual(qs, expected, attrgetter('pk'), False)
