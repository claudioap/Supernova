from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models import Model, TextField, ForeignKey, DateTimeField, DateField, BooleanField
from ckeditor.fields import RichTextField

from college.models import Place, TurnInstance, Building
from users.models import Profile


class Document(Model):
    author_user = ForeignKey(Profile, null=True, blank=True, on_delete=models.SET_NULL, related_name='document_author')
    author_group = ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)
    title = TextField(max_length=300)
    content = RichTextField()
    creation = DateField(auto_now_add=True)
    public = BooleanField(default=False)
    last_edition = DateTimeField(null=True, blank=True, default=None)
    last_editor = ForeignKey(Profile, null=True, blank=True, default=None, on_delete=models.SET_NULL,
                             related_name='document_editor')

    class Meta:
        ordering = ['creation']

    def __str__(self):
        return f'{self.title}, {self.author_user}'


class UserPermission(Model):
    document = ForeignKey(Document, on_delete=models.CASCADE)
    user = ForeignKey(Profile, on_delete=models.CASCADE)


class GroupPermission(Model):
    document = ForeignKey(Document, on_delete=models.CASCADE)
    group = ForeignKey(Group, on_delete=models.CASCADE)