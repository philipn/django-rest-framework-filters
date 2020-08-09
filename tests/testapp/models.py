from django.contrib.auth.models import User
from django.db import models
from django.db.models import Case, Value, When


class PostQuerySet(models.QuerySet):

    def annotate_is_published(self):
        return self.annotate(is_published=Case(
            When(publish_date__isnull=False, then=Value(True)),
            default=Value(False),
            output_field=models.BooleanField(),
        ))


class Note(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)


class Tag(models.Model):
    name = models.CharField(max_length=100)


class Blog(models.Model):
    name = models.CharField(max_length=100)


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    publish_date = models.DateField(null=True)

    blog = models.ForeignKey(Blog, null=True, on_delete=models.CASCADE)
    author = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    note = models.ForeignKey(Note, null=True, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)

    objects = PostQuerySet.as_manager()


class Cover(models.Model):
    comment = models.CharField(max_length=100)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class Page(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    previous_page = models.ForeignKey('self', null=True, on_delete=models.CASCADE)


class A(models.Model):
    title = models.CharField(max_length=100)
    b = models.ForeignKey('B', null=True, on_delete=models.CASCADE)


class B(models.Model):
    name = models.CharField(max_length=100)
    c = models.ForeignKey('C', null=True, on_delete=models.CASCADE)


class C(models.Model):
    title = models.CharField(max_length=100)
    a = models.ForeignKey('A', null=True, on_delete=models.CASCADE)


class Person(models.Model):
    name = models.CharField(max_length=100)
    best_friend = models.ForeignKey('self', null=True, on_delete=models.CASCADE)

    date_joined = models.DateField(auto_now_add=True)
    time_joined = models.TimeField(auto_now_add=True)
    datetime_joined = models.DateTimeField(auto_now_add=True)


# Models using `to_field`
class Customer(models.Model):
    name = models.CharField(max_length=80)
    ssn = models.CharField(max_length=9, unique=True)
    dob = models.DateField()


class Account(models.Model):
    TYPE_CHOICES = [
        ('c', 'Checking'),
        ('s', 'Savings'),
    ]
    customer = models.ForeignKey(Customer, to_field='ssn', on_delete=models.CASCADE)
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    name = models.CharField(max_length=80)
