from ckeditor.fields import RichTextField
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Model, ForeignKey, DateTimeField, CharField, URLField, IntegerField, TextField, \
    ManyToManyField

from college.models import Class
from synopses.models import Section
from users.models import User


class Exercise(Model):
    QA = 0  #: Question-answer pair
    MC = 1  #: Multiple choice
    QAG = 2  #: Question-answer group
    MCG = 3  #: Multiple choice group

    CONCLUSION_CHOICES = (
        (QA, 'Questão-resposta'),
        (MC, 'Escolha múltipla'),
        (QAG, 'Grupo questão-resposta'),
        (MCG, 'Grupo escolha múltipla')
    )

    introduction = RichTextField(null=True, blank=False, verbose_name='introduction')  #: Optional question introduction
    #: The :py:class:`users.models.User` which uploaded this exercise
    author = ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='contributed_exercises')
    #: Creation datetime
    datetime = DateTimeField(auto_now_add=True)
    #: Exercise type
    type = IntegerField(choices=CONCLUSION_CHOICES, verbose_name='tipo')
    #: Origin of this exercise
    source = CharField(max_length=100, null=True, blank=True, verbose_name='origem')
    #: Optional URL of the origin
    source_url = URLField(null=True, blank=True, verbose_name='endreço')
    #: :py:class:`synopses.models.Section` for which this exercise makes sense (m2m)
    synopses_sections = ManyToManyField(Section, verbose_name='secções de sínteses')
    content = JSONField()
    """
    Has JSON in the format when dealing with question-answer pairs::
    
        [{'question': x,
          'answer': y,
          'explanation': z},
          ...
        ]
    
    when the exercise is a multiple choice, the answer is an array and there's a additional ``correct_index`` field::
    
        [{'question': x,
          'answer': [a, b, c, d],
          'explanation': z,
          'correct_index': k},
          ...
        ]
    
    There are as many dictionaries as questions in the group. Singular exercises have a unitary length array
    """
    #: Time this exercise was successfully solved (should be redundant and act as cache)
    successes = IntegerField(default=0)
    #: Number of times users failed to solve this exercise (should be redundant and act as cache)
    failures = IntegerField(default=0)
    #: Number of times users skipped this exercise (should be redundant and act as cache)
    skips = IntegerField(default=0)


class UserExerciseLog:
    """
    Relation between :py:class:`users.models.User` and :py:class:`Exercise` which represents an attempt.
    """
    OPENED = 0  #: User opened the exercise
    SKIPPED = 1  #: User skipped the exercise
    WRONG = 2  #: User gave a wrong answer to the exercise
    DONE = 3  #: User solved the exercise

    CONCLUSION_CHOICES = (
        (OPENED, 'opened'),
        (SKIPPED, 'skipped'),
        (WRONG, 'wrong'),
        (DONE, 'done')
    )

    #: :py:class:`users.models.User` which attempted to solve this exercise
    user = ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='exercises')
    #: :py:class:`users.models.Exercise` being attempted
    exercise = ForeignKey(Exercise, on_delete=models.CASCADE, related_name='users')
    #: Attempt result
    status = IntegerField(choices=CONCLUSION_CHOICES)
    #: (Optional) Given answer
    given_answer = JSONField(null=True, blank=True)
    #: Attempt datetime
    datetime = DateTimeField(auto_now=True)


class WrongAnswerReport:
    """
    A user submitted report of an exercise which has a wrong answer.
    """
    #: :py:class:`users.models.User` reporter
    user = ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='wrong_answer_reports')
    #: :py:class:`Exercise` being reported
    exercise = ForeignKey(Exercise, on_delete=models.CASCADE, related_name='wrong_answer_reports')
    #: The issue
    reason = TextField()
