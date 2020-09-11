from django.conf import settings
from django.db.models import Max
from django.urls import reverse
from django.db import models as djm, transaction
from polymorphic.models import PolymorphicModel

from functools import reduce
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from ckeditor_uploader.fields import RichTextUploadingField

from users import models as users
from college import models as college
from documents import models as documents


def area_pic_path(area, filename):
    return f's/a/{area.id}/pic.{filename.split(".")[-1].lower()}'


class Area(djm.Model):
    """
    A field of knowledge
    """
    #: The title of the area
    title = djm.CharField(max_length=64)
    #: An image that illustrates the area
    image = djm.ImageField(null=True, blank=True, upload_to=area_pic_path)
    img_url = djm.TextField(null=True, blank=True)  # TODO deleteme

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title


def subarea_pic_path(subarea, filename):
    return f's/sa/{subarea.id}/pic.{filename.split(".")[-1].lower()}'


class Subarea(djm.Model):
    """
    A category inside a field of knowledge (area)
    """
    #: This subarea's title
    title = djm.CharField(max_length=256)
    #: An image that illustrates the area
    description = djm.TextField(max_length=1024, verbose_name='descrição')
    #: The :py:class:`synopses.models.Area` that owns this subarea
    area = djm.ForeignKey(Area, on_delete=djm.PROTECT, related_name='subareas')
    #: An image that illustrates the subarea
    image = djm.ImageField(null=True, blank=True, upload_to=subarea_pic_path, verbose_name='imagem')
    img_url = djm.TextField(null=True, blank=True, verbose_name='imagem (url)')  # TODO deleteme

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title


class Section(djm.Model):
    """
    A synopsis section, belonging either directly or indirectly to some subarea.
    Sections form a knowledge graph.
    """
    #: The title of the section
    title = djm.CharField(max_length=256)
    #: The markdown content
    content_md = MarkdownxField(null=True, blank=True)
    #: The CKEditor-written content (legacy format)
    content_ck = RichTextUploadingField(null=True, blank=True, config_name='complex')
    #: Subareas where this section directly fits in
    subarea = djm.ForeignKey(
        Subarea,
        null=True,
        blank=True,
        on_delete=djm.PROTECT,
        verbose_name='subarea',
        related_name='sections')
    #: Sections that have this section as a subsection
    parents = djm.ManyToManyField(
        'self',
        through='SectionSubsection',
        symmetrical=False,
        blank=True,
        related_name='children',
        verbose_name='parents')
    #: Sections that reference this section as a requirement (dependants)
    requirements = djm.ManyToManyField(
        'self',
        blank=True,
        related_name='required_by',
        verbose_name='requisitos',
        symmetrical=False)
    classes = djm.ManyToManyField(
        college.Class,
        blank=True,
        through='ClassSection',
        related_name='synopsis_sections')
    #: Whether this section has been validated as correct by a teacher
    validated = djm.BooleanField(default=False)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return f"({self.id}) {self.title}"

    @property
    def content(self):
        if self.content_md:
            return markdownify(self.content_md)
        return self.content_ck

    def content_reduce(self):
        """
        Detects the absence of content and nullifies the field in that case.
        """
        # TODO, do this properly
        if self.content_md is not None and len(self.content_md) < 10:
            self.content_md = None
        if self.content_ck is not None and len(self.content_ck) < 10:
            self.content_ck = None

    def most_recent_edit(self, editor):
        return SectionLog.objects.get(section=self, author=editor).order_by('timestamp')

    def compact_indexes(self):
        index = 0
        for rel in self.children_intermediary.order_by('index').all():
            if index != rel.index:
                rel.index = index
                rel.save()
            index += 1


class ClassSection(djm.Model):
    """
    Model which links a section to a College Class
    """
    corresponding_class = djm.ForeignKey(college.Class, on_delete=djm.PROTECT, related_name='synopsis_sections_rel')
    section = djm.ForeignKey(Section, on_delete=djm.CASCADE, related_name='classes_rel')
    index = djm.IntegerField()

    class Meta:
        unique_together = [('section', 'corresponding_class'), ('index', 'corresponding_class')]

    def __str__(self):
        return f'{self.section} annexed to {self.corresponding_class}.'


class SectionSubsection(djm.Model):
    """
    Model which links pairs of parent-children sections.
    """
    #: The child :py:class:`synopses.models.Section`
    section = djm.ForeignKey(Section, on_delete=djm.CASCADE, related_name='parents_intermediary')
    #: The parent :py:class:`synopses.models.Section`
    parent = djm.ForeignKey(Section, on_delete=djm.CASCADE, related_name='children_intermediary')
    #: The position where the referenced section is indexed in the parent
    index = djm.IntegerField(null=False)

    class Meta:
        ordering = ('parent', 'index',)
        unique_together = [('section', 'parent'), ('index', 'parent')]

    def __str__(self):
        return f'{self.parent} -({self.index})-> {self.section}.'

    def save(self, **kwargs):
        if self.index is None:
            biggest_index = SectionSubsection.objects.filter(parent=self.parent).aggregate(Max('index'))['index__max']
            self.index = 0 if biggest_index is None else biggest_index + 1
        djm.Model.save(self)


class SectionLog(djm.Model):
    """
    The changelog for a section
    """
    author = djm.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=djm.SET_NULL,
                            related_name='_section_logs')
    section = djm.ForeignKey(Section, on_delete=djm.CASCADE, related_name='log_entries')
    timestamp = djm.DateTimeField(auto_now_add=True)
    previous_content = djm.TextField(blank=True, null=True)  # TODO Change to diff

    def __str__(self):
        return f'{self.author} edited {self.section} @ {self.timestamp}.'


class SectionSource(djm.Model):
    """
    Sources the content that a :py:class:`synopses.models.Section` presents.
    """
    #: :py:class:`synopses.models.Section` which references this source
    section = djm.ForeignKey(Section, on_delete=djm.CASCADE, related_name='sources')
    #: Verbose title for this resource
    title = djm.CharField(max_length=256, null=True, blank=True)
    #: Location containing the referenced source
    url = djm.URLField(blank=True, null=True, verbose_name='endreço')

    class Meta:
        ordering = ('section', 'title', 'url')
        unique_together = [('section', 'url'), ]


class SectionResource(PolymorphicModel):
    """
    A resource that is referenced by a :py:class:`synopses.models.Section`.
    Resources are aids aimed at easing the learning experience.
    """
    #: :py:class:`synopses.models.Section` which references this resource
    section = djm.ForeignKey(Section, on_delete=djm.CASCADE, related_name='resources')
    #: Verbose title for this resource
    title = djm.CharField(max_length=256, null=True, blank=True)

    @property
    def template_title(self):
        return "Sem título" if self.title is None else self.title

    @property
    def template_url(self):
        return None


class SectionDocumentResource(SectionResource):
    #: Resource :py:class:`documents.models.Document`
    document = djm.ForeignKey(documents.Document, on_delete=djm.PROTECT, related_name='section_resources')

    @property
    def template_title(self):
        return self.document.title if self.title is None else self.title

    @property
    def template_url(self):
        return reverse('college:department', args=[self.document.id])


class SectionWebResource(SectionResource):
    #: Resource location
    url = djm.URLField()

    @property
    def template_title(self):
        return self.url if self.title is None else self.title

    @property
    def template_url(self):
        return self.url


class Exercise(djm.Model):
    """
    An exercise anyone can try to solve
    """
    #: | Holds three types of objects.
    #: | - Question-answer pairs
    #: `{type:write, enunciation: "...", answer:"..."}`
    #: | - Multiple question
    #: `{type:select, enunciation: "...", candidates:["...", ...], answerIndex:x}`
    #: | - Multiple subproblems (recursive)
    #: - `{type:group, enunciation: "...", subproblems: [object, ...]}`
    content = djm.JSONField()

    #: The :py:class:`users.models.User` which uploaded this exercise
    author = djm.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=djm.SET_NULL,
        related_name='contributed_exercises')
    #: Creation datetime
    datetime = djm.DateTimeField(auto_now_add=True)
    #: Origin of this exercise
    source = djm.CharField(null=True, blank=True, max_length=256, verbose_name='origem')
    #: Optional URL of the origin
    source_url = djm.URLField(null=True, blank=True, verbose_name='endreço')
    #: :py:class:`synopses.models.Section` for which this exercise makes sense (m2m)
    synopses_sections = djm.ManyToManyField(
        Section,
        blank=True,
        verbose_name='secções de sínteses',
        related_name='exercises')

    #: Time this exercise was successfully solved (should be redundant and act as cache)
    successes = djm.IntegerField(default=0)
    #: Number of times users failed to solve this exercise (should be redundant and act as cache)
    failures = djm.IntegerField(default=0)
    #: Number of times users skipped this exercise (should be redundant and act as cache)
    skips = djm.IntegerField(default=0)

    def count_problems(self):
        return Exercise._count_problems(self.content)

    @staticmethod
    def _count_problems(exercise):
        if exercise['type'] == "group":
            return reduce(lambda x, y: x + y, map(Exercise._count_problems, exercise['subproblems']))
        return 1

    @property
    def render_html(self):
        return self.__render_html_aux(self.content)

    @staticmethod
    def __render_html_aux(problem):
        if (type := problem['type']) == 'group':
            subproblems = "".join(
                [f"<div>{Exercise.__render_html_aux(subproblem)}</div><hr>"
                 for subproblem in problem['subproblems']])
            return '<h2>Grupo</h2>' \
                   f'<blockquote class="exercise-enunciation">{markdownify(problem["enunciation"])}</blockquote>' \
                   f'<div class="subexercises">{subproblems[:-4]}</div>'  # [:-4] ignores last <hr>
        elif type == 'write':
            return '<h2>Questão</h2>' \
                   f'<blockquote class="exercise-enunciation">{markdownify(problem["enunciation"])}</blockquote>' \
                   '<h2>Resposta</h2>' \
                   f'<div class="exercise-answer">{markdownify(problem["answer"])}</div>'
        elif type == 'select':
            answers = "".join([f"{chr(ord('A') + index)}) {markdownify(problem['candidates'][index])}" for index in problem['answerIndexes']])
            return '<h2>Questão</h2>' \
                   f'<blockquote class="exercise-enunciation">{markdownify(problem["enunciation"])}</blockquote>' \
                   '<ol type="A" class="exercise-answer-candidates">' \
                   f'{"".join(["<li>%s</li>" % markdownify(candidate) for candidate in problem["candidates"]])}' \
                   '</ol>' \
                   '<h2>Resposta</h2>' \
                   '<div class="exercise-answer">' \
                   f'{answers}' \
                   '</div>'
        else:
            raise Exception("Attempted to render an exercise which is not fully implemented")


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
    user = djm.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=djm.SET_NULL, related_name='exercises')
    #: :py:class:`users.models.Exercise` being attempted
    exercise = djm.ForeignKey(Exercise, on_delete=djm.CASCADE, related_name='users')
    #: Attempt result
    status = djm.IntegerField(choices=CONCLUSION_CHOICES)
    #: (Optional) Given answer
    given_answer = djm.JSONField(null=True, blank=True)
    #: Attempt datetime
    datetime = djm.DateTimeField(auto_now=True)


class WrongAnswerReport:
    """
    An user submitted report of an exercise which has a wrong answer.
    """
    #: :py:class:`users.models.User` reporter
    user = djm.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=djm.SET_NULL,
        related_name='wrong_answer_reports')
    #: :py:class:`Exercise` being reported
    exercise = djm.ForeignKey(Exercise, on_delete=djm.CASCADE, related_name='wrong_answer_reports')
    #: The issue
    reason = djm.TextField()


class Postable(djm.Model):
    #: Posted content
    content = MarkdownxField()
    #: Creation datetime
    creation_timestamp = djm.DateTimeField(auto_now_add=True)

    # Cached fields
    upvotes = djm.IntegerField(default=0)
    downvotes = djm.IntegerField(default=0)

    class Meta:
        ordering = ('creation_timestamp',)

    @property
    def content_html(self):
        return markdownify(self.content)

    def cache_votes(self):
        self.upvotes = PostableVote.objects.filter(to=self, type=PostableVote.UPVOTE).count()
        self.downvotes = PostableVote.objects.filter(to=self, type=PostableVote.DOWNVOTE).count()
        self.save()

    @property
    def vote_balance(self):
        if self.upvotes is None:
            self.cache_votes()
        return self.upvotes - self.downvotes

    def set_vote(self, user, vote_type):
        with transaction.atomic():
            votes = self.votes.filter(user=user).all()
            has_upvote = False
            has_downvote = False
            # Counted this way since more types of votes might be implemented
            for vote in votes:
                if vote.type == PostableVote.UPVOTE:
                    has_upvote = True
                if vote.type == PostableVote.DOWNVOTE:
                    has_downvote = True

            if vote_type == PostableVote.UPVOTE or vote_type == PostableVote.DOWNVOTE:
                upvote = vote_type == PostableVote.UPVOTE
                if upvote:
                    if has_downvote:
                        self.votes.filter(user=user, type=PostableVote.DOWNVOTE).update(type=PostableVote.UPVOTE)
                        self.upvotes += 1
                        self.downvotes -= 1
                    elif not has_upvote:
                        PostableVote.objects.create(to=self, user=user, type=PostableVote.UPVOTE)
                        self.upvotes += 1
                else:
                    if has_upvote:
                        self.votes.filter(user=user, type=PostableVote.UPVOTE).update(type=PostableVote.DOWNVOTE)
                        self.upvotes -= 1
                        self.downvotes += 1
                    elif not has_downvote:
                        PostableVote.objects.create(to=self, user=user, type=PostableVote.DOWNVOTE)
                        self.downvotes += 1
            self.save()


class Question(users.Activity, users.Subscriptible, Postable):
    """
    A generic question, usually about an exercise.
    """
    #: A descriptive title
    title = djm.CharField(max_length=128)
    #: The related :py:class:`synopses.models.Section`
    linked_sections = djm.ManyToManyField(
        Section,
        blank=True,
        verbose_name='Secções relacionadas',
        related_name='linked_questions')
    #: The related :py:class:`exercises.models.Exercise`
    linked_exercises = djm.ManyToManyField(
        Exercise,
        blank=True,
        verbose_name='Exercícios relacionados',
        related_name='linked_questions')
    #: The related :py:class:`college.models.Class`
    linked_classes = djm.ManyToManyField(
        college.Class,
        blank=True,
        verbose_name='Unidades curriculares relacionadas',
        related_name='linked_questions')
    #: Question that makes this one redundant
    duplication_of = djm.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=djm.SET_NULL,
        related_name='duplicates')

    def __str__(self):
        return f"questão '{self.title}'"


class QuestionAnswer(users.Activity, users.Subscriptible, Postable):
    """
    An answer to a Question
    """
    #: :py:class:`Postable` to which this answer refers
    to = djm.ForeignKey(
        Question,
        on_delete=djm.PROTECT,
        related_name='answers')
    #: Signals if this answer is the accepted answer
    accepted = djm.BooleanField(default=False)

    def __str__(self):
        return f"resposta a {self.to}"


class PostableComment(users.Activity, users.Subscriptible, Postable):
    """
    A comment to any object which inherits from :py:class:`Postable`
    """
    #: :py:class:`Postable` to which this comment refers
    to = djm.ForeignKey(
        Postable,
        on_delete=djm.PROTECT,
        related_name='comments')

    def __str__(self):
        return f"comentario em {self.to}"


class PostableVote(users.Activity):
    """
    A vote in a question, answer or another comment
    Having choices instead of something simpler (boolean?) is due to the possibility of expanding later on
    to having more vote types (favorite, ... ?)
    """
    UPVOTE = 0
    DOWNVOTE = 1
    VOTE_CHOICES = [
        (UPVOTE, 'Upvote'),
        (DOWNVOTE, 'Downvote'),
    ]
    #: Type of vote. Right now only up and down votes.
    type = djm.IntegerField(choices=VOTE_CHOICES)
    #: Postable to which this vote refers
    to = djm.ForeignKey(
        Postable,
        on_delete=djm.PROTECT,
        related_name='votes')

    def __str__(self):
        return f"voto {self.get_type_display()} em {self.to}"
