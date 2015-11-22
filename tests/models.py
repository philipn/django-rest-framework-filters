
from django.db import models
from django.contrib.auth.models import User


class Note(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    author = models.ForeignKey(User)


class Post(models.Model):
    note = models.ForeignKey(Note)
    content = models.TextField()


class Cover(models.Model):
    comment = models.CharField(max_length=100)
    post = models.ForeignKey(Post)


class Page(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    previous_page = models.ForeignKey('self', null=True)


class A(models.Model):
    title = models.CharField(max_length=100)
    b = models.ForeignKey('B', null=True)


class C(models.Model):
    title = models.CharField(max_length=100)
    a = models.ForeignKey(A, null=True)


class B(models.Model):
    name = models.CharField(max_length=100)
    c = models.ForeignKey(C, null=True)


class Person(models.Model):
    name = models.CharField(max_length=100)
    best_friend = models.ForeignKey('self', null=True)

    date_joined = models.DateField(auto_now=True)
    time_joined = models.TimeField(auto_now=True)
    datetime_joined = models.DateTimeField(auto_now=True)


class Tag(models.Model):
    name = models.CharField(max_length=100)


class BlogPost(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    tags = models.ManyToManyField(Tag, null=True)
