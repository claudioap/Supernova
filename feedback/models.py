from django.db import models
from django.db.models import Model, TextField, ForeignKey, DateTimeField, ManyToManyField, BooleanField
from users.models import Profile


class Comment(Model):
    author = ForeignKey(Profile, null=True, on_delete=models.SET_NULL)
    content = TextField(max_length=1024)
    datetime = DateTimeField(auto_now_add=True)


class Entry(Model):
    title = TextField(max_length=100)
    description = TextField()
    author = ForeignKey(Profile, null=True, on_delete=models.SET_NULL)
    comments = ManyToManyField(Comment, through='EntryComment')
    closed = BooleanField()
    reason = TextField(max_length=100)

    class Meta:
        unique_together = ['title', 'author']
        verbose_name_plural = 'entries'


class EntryComment(Model):
    comment = ForeignKey(Comment, on_delete=models.CASCADE)
    entry = ForeignKey(Entry, on_delete=models.CASCADE)
    positive = BooleanField()
