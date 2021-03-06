import json

import reversion
from dal import autocomplete
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, F, Max
from django.forms import HiddenInput
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.contrib.auth.decorators import permission_required, login_required
from django.db import models as djm, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings

from markdownx.widgets import MarkdownxWidget
from reversion.models import Version

from supernova.utils import comparison_html
from supernova.views import build_base_context
from learning import models as m
from learning import forms as f
from college import models as college
from users.utils import get_students


def areas_view(request):
    context = build_base_context(request)
    context['pcode'] = 'l_synops'
    context['title'] = 'Sínteses - Areas de estudo'
    context['areas'] = m.Area.objects.prefetch_related('subareas').all()
    context['classes'] = \
        college.Class.objects \
            .select_related('department') \
            .annotate(section_count=Count('synopsis_sections')) \
            .filter(section_count__gt=0) \
            .order_by('section_count') \
            .reverse()
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')}]
    return render(request, 'learning/areas.html', context)


def area_view(request, area_id):
    area = get_object_or_404(
        m.Area.objects,
        id=area_id)
    subareas = area.subareas.annotate(section_count=Count('sections'))

    context = build_base_context(request)
    context['pcode'] = 'l_synopses_area'
    context['title'] = 'Sínteses - Categorias de %s' % area.title
    context['area'] = area
    context['subareas'] = subareas
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': area.title, 'url': reverse('learning:area', args=[area_id])}]
    return render(request, 'learning/area.html', context)


def subarea_view(request, subarea_id):
    subarea = get_object_or_404(
        m.Subarea.objects.select_related('area'),
        id=subarea_id)
    area = subarea.area
    sections = subarea.sections.annotate(children_count=Count('children'))
    context = build_base_context(request)
    context['pcode'] = 'l_synopses_subarea'
    context['title'] = 'Sínteses - %s (%s)' % (subarea.title, area.title)
    context['sections'] = sections
    context['subarea'] = subarea
    context['area'] = area
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': area.title, 'url': reverse('learning:area', args=[area.id])},
                          {'name': subarea.title, 'url': reverse('learning:subarea', args=[subarea_id])}]
    return render(request, 'learning/subarea.html', context)


@login_required
@permission_required('learning.add_subarea', raise_exception=True)
def subarea_create_view(request, area_id):
    area = get_object_or_404(m.Area, id=area_id)

    if request.method == 'POST':
        form = f.SubareaForm(data=request.POST)
        if form.is_valid():
            with reversion.create_revision():
                new_subarea = form.save()
                reversion.set_user(request.user)
            return HttpResponseRedirect(reverse('learning:subarea', args=[new_subarea.id]))
    else:
        form = f.SubareaForm(initial={'area': area})
        form.fields['area'].widget = HiddenInput()

    context = build_base_context(request)
    context['pcode'] = 'l_synopses_subarea'
    context['title'] = 'Criar nova categoria de "%s"' % area.title
    context['area'] = area
    context['form'] = form
    context['action_page'] = reverse('learning:subarea_create', args=[area_id])
    context['action_name'] = 'Criar'
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': area.title, 'url': reverse('learning:area', args=[area.id])},
                          {'name': 'Propor nova categoria', 'url': reverse('learning:subarea_create', args=[area_id])}]
    return render(request, 'learning/generic_form.html', context)


@login_required
@permission_required('learning.change_subarea', raise_exception=True)
def subarea_edit_view(request, subarea_id):
    subarea = get_object_or_404(m.Subarea, id=subarea_id)
    area = subarea.area

    if request.method == 'POST':
        form = f.SubareaForm(request.POST, request.FILES, instance=subarea)
        if form.is_valid():
            with reversion.create_revision():
                form.save()
                reversion.set_user(request.user)
            return HttpResponseRedirect(reverse('learning:subarea', args=[subarea_id]))
    else:
        form = f.SubareaForm(instance=subarea)

    context = build_base_context(request)
    context['pcode'] = 'l_synopses_subarea'
    context['title'] = 'Editar categoria "%s"' % subarea.title
    context['form'] = form
    context['action_page'] = reverse('learning:subarea_edit', args=[subarea_id])
    context['action_name'] = 'Aplicar alterações'
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': area.title, 'url': reverse('learning:area', args=[area.id])},
                          {'name': subarea.title, 'url': reverse('learning:subarea', args=[subarea_id])},
                          {'name': 'Editar', 'url': reverse('learning:subarea_edit', args=[subarea_id])}]
    return render(request, 'learning/generic_form.html', context)


def __section_common(section, context):
    """
    Code that is common to every section view.
    :param section: The section that is being shown
    :param context: The template context variable
    """
    context['pcode'] = 'l_synopses_section'
    context['section'] = section
    children = m.Section.objects \
        .filter(parents_intermediary__parent=section) \
        .order_by('parents_intermediary__index').all()
    parents = m.Section.objects \
        .filter(children_intermediary__section=section) \
        .order_by('children_intermediary__index').all()
    context['children'] = children
    context['parents'] = parents
    last_timestamp = section.log_entries.aggregate(Max('timestamp'))
    if last_timestamp is not None:
        last_timestamp = last_timestamp['timestamp__max']
    context['last_update'] = last_timestamp
    context['author_log'] = section.log_entries.distinct('author')


def section_view(request, section_id):
    """
    View where a section is displayed as an isolated object.
    """
    section = get_object_or_404(
        m.Section.objects
            .select_related('subarea')
            .prefetch_related('classes')
            .annotate(question_count=Count('linked_questions', distinct=True),
                      exercise_count=Count('exercises', distinct=True)),
        id=section_id)
    context = build_base_context(request)
    __section_common(section, context)
    context['title'] = section.title
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': '...', 'url': '#'},
                          {'name': section.title, 'url': '#'}]
    return render(request, 'learning/section.html', context)


def subsection_view(request, parent_id, child_id):
    """
    View where a section is displayed as a part of another section.
    """
    parent = get_object_or_404(m.Section, id=parent_id)
    child = get_object_or_404(
        m.Section.objects
            .prefetch_related('classes')
            .annotate(question_count=Count('linked_questions', distinct=True),
                      exercise_count=Count('exercises', distinct=True)),
        id=child_id)
    context = build_base_context(request)
    __section_common(child, context)
    context['title'] = '%s - %s' % (child.title, parent.title)
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': '...', 'url': '#'},
                          {'name': parent.title, 'url': reverse('learning:section', args=[parent_id])},
                          {'name': child.title, 'url': '#'}]
    return render(request, 'learning/section.html', context)


def subarea_section_view(request, subarea_id, section_id):
    """
    View where a section is displayed as direct child of a subarea.
    """
    section = get_object_or_404(
        m.Section.objects
            .select_related('subarea__area')
            .prefetch_related('classes')
            .annotate(question_count=Count('linked_questions', distinct=True),
                      exercise_count=Count('exercises', distinct=True)),
        id=section_id)
    subarea = section.subarea
    if subarea.id != subarea_id:
        raise Http404('Mismatched section')
    area = subarea.area
    context = build_base_context(request)
    __section_common(section, context)
    context['title'] = '%s - %s' % (section.title, area.title)
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': area.title, 'url': reverse('learning:area', args=[area.id])},
                          {'name': subarea.title, 'url': reverse('learning:subarea', args=[subarea_id])},
                          {'name': section.title, 'url': '#'}]
    return render(request, 'learning/section.html', context)


def section_authors_view(request, section_id):
    section = get_object_or_404(m.Section.objects.prefetch_related('log_entries__author'), id=section_id)
    context = build_base_context(request)
    context['pcode'] = 'l_synopses_section'
    context['title'] = f"Autores de {section.title}"
    context['section'] = section
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': '...', 'url': '#'},
                          {'name': section.title, 'url': reverse('learning:section', args=[section_id])},
                          {'name': 'Autores', 'url': '#'}]
    return render(request, 'learning/section_authors.html', context)


@login_required
@permission_required('learning.add_section', raise_exception=True)
def section_create_view(request, subarea_id=None, parent_id=None):
    subarea, parent = None, None  # Suppress warnings
    if subarea_id is not None:
        subarea = get_object_or_404(m.Subarea, id=subarea_id)
    if parent_id is not None:
        parent = get_object_or_404(m.Section, id=parent_id)

    sources_formset = f.SectionSourcesFormSet(prefix="sources")
    web_resources_formset = f.SectionWebpageResourcesFormSet(prefix="wp_resources")
    # doc_resources_formset = f.SectionDocumentResourcesFormSet(prefix="doc_resources")
    if request.method == 'POST':
        section_form = f.SectionCreateForm(data=request.POST)
        if section_form.is_valid():
            if subarea:
                # Save the new section atomically (all or nothing)
                with transaction.atomic():
                    with reversion.create_revision():
                        section = section_form.save()
                        section.subarea = subarea
                        section.save()
                        reversion.set_user(request.user)
            else:
                # Obtain the requested index
                index = m.SectionSubsection.objects \
                    .filter(parent=parent) \
                    .aggregate(Max('index'))['index__max']
                index = 0 if index is None else index + 1

                # Save the new section atomically (all or nothing)
                with transaction.atomic():
                    with reversion.create_revision():
                        section = section_form.save()
                        section_parent_rel = m.SectionSubsection(parent=parent, section=section, index=index)
                        section_parent_rel.save()
                        reversion.set_user(request.user)

            sources_formset = f.SectionSourcesFormSet(
                request.POST,
                prefix="sources",
                instance=section)
            web_resources_formset = f.SectionWebpageResourcesFormSet(
                request.POST,
                prefix="wp_resources",
                instance=section)
            # doc_resources_formset = f.SectionDocumentResourcesFormSet(
            #     request.POST,
            #     prefix="doc_resources",
            #     instance=section)
            if sources_formset.is_valid():
                sources_formset.save()
            if web_resources_formset.is_valid():
                # for form in web_resources_formset:  # For some reason this passes the unit tests
                #     form.save()
                web_resources_formset.save()  # While this doesn't... go figure!
            # if doc_resources_formset.is_valid():
            #     # for form in doc_resources_formset:  # For some reason this passes the unit tests
            #     #     form.save()
            #     doc_resources_formset.save()

            # Redirect to the newly created section
            if subarea:
                return HttpResponseRedirect(reverse('learning:subarea_section', args=[subarea_id, section.id]))
            else:
                return HttpResponseRedirect(reverse('learning:subsection', args=[parent_id, section.id]))
    else:
        section_form = f.SectionCreateForm()

    context = build_base_context(request)
    context['pcode'] = 'l_synopses_section'
    context['form'] = section_form
    context['sources_formset'] = sources_formset
    context['web_resources_formset'] = web_resources_formset
    # context['doc_resources_formset'] = doc_resources_formset
    if subarea:
        area = subarea.area
        context['title'] = 'Criar secção em "%s"' % subarea.title
        context['sub_nav'] = [
            {'name': 'Sínteses', 'url': reverse('learning:areas')},
            {'name': area.title, 'url': reverse('learning:area', args=[area.id])},
            {'name': subarea.title, 'url': reverse('learning:subarea', args=[subarea.id])},
            {'name': 'Criar secção'}]
        context['action_page'] = reverse('learning:subarea_section_create', args=[subarea_id])
    else:
        context['title'] = 'Criar nova entrada em %s' % parent.title
        context['sub_nav'] = [
            {'name': 'Sínteses', 'url': reverse('learning:areas')},
            {'name': '...'},
            {'name': parent.title, 'url': reverse('learning:section', args=[parent_id])},
            {'name': 'Criar secção', 'url': '#'}]
        context['action_page'] = reverse('learning:subsection_create', args=[parent_id])
    return render(request, 'learning/section_management.html', context)


@login_required
@permission_required('learning.change_section', raise_exception=True)
def section_edit_view(request, section_id):
    section = get_object_or_404(m.Section, id=section_id)
    if request.method == 'POST':
        section_form = f.SectionEditForm(data=request.POST, instance=section)
        sources_formset = f.SectionSourcesFormSet(
            request.POST, instance=section, prefix="sources")
        web_resources_formset = f.SectionWebpageResourcesFormSet(
            request.POST, instance=section, prefix="wp_resources")
        # doc_resources_formset = f.SectionDocumentResourcesFormSet(
        #     request.POST, instance=section, prefix="doc_resources")
        if section_form.is_valid() \
                and sources_formset.is_valid() \
                and web_resources_formset.is_valid():
                # and doc_resources_formset.is_valid():
            with reversion.create_revision():
                section = section_form.save()
                sources_formset.save()
                # doc_resources_formset.save()
                web_resources_formset.save()
                section.compact_indexes()
                reversion.set_user(request.user)
            # Redirect user to the updated section
            return HttpResponseRedirect(reverse('learning:section', args=[section.id]))
    else:
        section_form = f.SectionEditForm(instance=section)
        sources_formset = f.SectionSourcesFormSet(instance=section, prefix="sources")
        web_resources_formset = f.SectionWebpageResourcesFormSet(instance=section, prefix="wp_resources")
        doc_resources_formset = f.SectionDocumentResourcesFormSet(instance=section, prefix="doc_resources")

    context = build_base_context(request)
    context['pcode'] = 'l_synopses_section'
    context['title'] = 'Editar %s' % section.title
    context['section'] = section
    context['form'] = section_form
    context['sources_formset'] = sources_formset
    context['web_resources_formset'] = web_resources_formset
    # context['doc_resources_formset'] = doc_resources_formset
    context['action_page'] = reverse('learning:section_edit', args=[section_id])
    context['action_name'] = 'Editar'
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': '...', 'url': '#'},
                          {'name': section.title, 'url': reverse('learning:section', args=[section_id])},
                          {'name': 'Editar'}]
    return render(request, 'learning/section_management.html', context)


# Class related views
def class_sections_view(request, class_id):
    class_ = get_object_or_404(college.Class, id=class_id)
    context = build_base_context(request)
    context['pcode'] = 'l_synopses_class_section'
    context['title'] = "Sintese de %s" % class_.name
    context['synopsis_class'] = class_
    context['sections'] = class_.synopsis_sections \
        .order_by('classes_rel__index') \
        .annotate(exercise_count=Count('exercises'))
    context['expand'] = 'expand' in request.GET
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': class_.name, 'url': reverse('learning:class', args=[class_id])}]
    return render(request, 'learning/class_sections.html', context)


def class_section_view(request, class_id, section_id):
    class_synopsis_section = get_object_or_404(
        m.ClassSection.objects
            .select_related('corresponding_class'),
        section_id=section_id, corresponding_class_id=class_id)
    class_ = class_synopsis_section.corresponding_class
    # TODO move the question_count and exercise_count variable_count vars to the context
    # in order to avoid this duplicated query (section could be select_related in the ClassSection query)
    section = m.Section.objects \
        .annotate(question_count=Count('linked_questions', distinct=True),
                  exercise_count=Count('exercises', distinct=True)) \
        .get(id=section_id)

    context = build_base_context(request)
    __section_common(section, context)
    context['title'] = '%s (%s)' % (section.title, class_.name)
    context['synopsis_class'] = class_
    context['section'] = section
    # FIXME old code to navigate from one section to the next in the same class
    # Get sections of this class, take the one indexed before and the one after.
    # related_sections = m.ClassSection.objects \
    #     .filter(corresponding_class=class_).order_by('index')
    # previous_section = related_sections.filter(index__lt=class_synopsis_section.index).last()
    # next_section = related_sections.filter(index__gt=class_synopsis_section.index).first()
    # if previous_section:
    #     context['previous_section'] = previous_section.section
    # if next_section:
    #     context['next_section'] = next_section.section
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': class_.name, 'url': reverse('learning:class', args=[class_id])},
                          {'name': section.title,
                           'url': reverse('learning:class_section', args=[class_id, section_id])}]
    return render(request, 'learning/section.html', context)


@staff_member_required
def class_manage_sections_view(request, class_id):
    class_ = get_object_or_404(college.Class, id=class_id)
    context = build_base_context(request)
    context['pcode'] = 'l_synopses_manage_sections'
    context['title'] = "Editar secções na sintese de %s" % class_.name
    context['synopsis_class'] = class_
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': class_.name, 'url': reverse('learning:class', args=[class_id])},
                          {'name': 'Secções', 'url': reverse('learning:class_manage', args=[class_id])}]
    return render(request, 'learning/class_management.html', context)


def section_exercises_view(request, section_id):
    section = get_object_or_404(
        m.Section.objects.prefetch_related('exercises'),
        id=section_id)
    context = build_base_context(request)
    context['pcode'] = 'l_synopses_section_exercises'
    context['title'] = "Exercicios em %s" % section.title
    context['section'] = section
    context['sub_nav'] = [{'name': 'Sínteses', 'url': reverse('learning:areas')},
                          {'name': '...', 'url': '#'},
                          {'name': section.title, 'url': reverse('learning:section', args=[section_id])},
                          {'name': 'Exercícios'}]
    return render(request, 'learning/section_exercises.html', context)


def exercises_view(request):
    context = build_base_context(request)
    context['pcode'] = 'l_exercises'
    context['title'] = 'Exercícios'
    context['department_exercises'] = college.Department.objects.filter(extinguished=False) \
        .annotate(exercise_count=djm.Count('classes__synopsis_sections__exercises')) \
        .order_by('name') \
        .all()
    context['exercise_count'] = m.Exercise.objects.count()
    if not request.user.is_anonymous and request.user.is_student:
        primary_students, context['secondary_students'] = get_students(request.user)
        context['classes'] = college.Class.objects \
            .annotate(exercise_count=djm.Count('synopsis_sections__exercises')) \
            .filter(instances__enrollments__student__in=primary_students) \
            .order_by('name') \
            .all()
    context['sub_nav'] = [{'name': 'Exercicios', 'url': reverse('learning:exercises')}]
    return render(request, 'learning/exercises.html', context)


def exercise_view(request, exercise_id):
    exercise = get_object_or_404(
        m.Exercise.objects
            .select_related('author')
            .annotate(question_count=Count('linked_questions')),
        id=exercise_id)
    context = build_base_context(request)
    context['pcode'] = 'l_exercises'
    context['title'] = f'Exercício #{exercise.id}'
    context['exercise'] = exercise
    context['classes'] = college.Class.objects.filter(synopsis_sections__exercises=exercise).distinct()
    context['sub_nav'] = [{'name': 'Exercícios', 'url': reverse('learning:exercises')},
                          {'name': f'#{exercise_id}',
                           'url': reverse('learning:exercise', args=[exercise_id])}]
    return render(request, 'learning/exercise.html', context)


@login_required
@permission_required('learning.add_exercise', raise_exception=True)
def create_exercise_view(request):
    if request.method == 'POST':
        form = f.ExerciseForm(request.POST)
        if form.is_valid():
            with reversion.create_revision():
                exercise = form.save(commit=False)
                exercise.author = request.user
                exercise.save()
                form.save_m2m()
                reversion.set_user(request.user)
            return redirect('learning:exercise', exercise_id=exercise.id)
    else:
        if 'section' in request.GET:
            section = get_object_or_404(m.Section, id=request.GET['section'])
            form = f.ExerciseForm(initial={'synopses_sections': [section, ]})
        else:
            form = f.ExerciseForm()

    context = build_base_context(request)
    context['pcode'] = 'l_exercises'
    context['title'] = 'Submeter exercício'
    context['form'] = form
    editor = MarkdownxWidget().render(name='', value='', attrs=dict())
    context['markdown_editor'] = editor
    context['sub_nav'] = [{'name': 'Exercícios', 'url': reverse('learning:exercises')},
                          {'name': 'Submeter exercício', 'url': reverse('learning:exercise_create')}]
    return render(request, 'learning/editor.html', context)


@login_required
@permission_required('learning.change_exercise', raise_exception=True)
def edit_exercise_view(request, exercise_id):
    exercise = get_object_or_404(m.Exercise, id=exercise_id)
    if request.method == 'POST':
        form = f.ExerciseForm(request.POST, instance=exercise)
        if form.is_valid():
            with reversion.create_revision():
                exercise = form.save()
                reversion.set_user(request.user)
            return redirect('learning:exercise', exercise_id=exercise.id)
    else:
        form = f.ExerciseForm(instance=exercise)

    context = build_base_context(request)
    context['pcode'] = 'l_exercises'
    context['title'] = f'Editar exercício #{exercise.id}'
    context['form'] = form
    context['sub_nav'] = [{'name': 'Exercícios', 'url': reverse('learning:exercises')},
                          {'name': f'#{exercise_id}', 'url': reverse('learning:exercise', args=[exercise_id])},
                          {'name': 'Editar', 'url': reverse('learning:exercise_edit', args=[exercise_id])}]
    return render(request, 'learning/editor.html', context)


def department_exercises_view(request, department_id):
    department = get_object_or_404(college.Department, id=department_id)
    context = build_base_context(request)
    context['pcode'] = 'l_exercises'
    context['title'] = f'Exercícios de {department.classes}'
    context['department'] = department
    if not request.user.is_anonymous and request.user.is_student:
        user_students = request.user.students.all()
        current_class_ids = department.classes \
            .filter(instances__enrollments__student__in=user_students,
                    instances__year=settings.COLLEGE_YEAR,
                    instances__period=settings.COLLEGE_PERIOD) \
            .distinct() \
            .values_list('id', flat=True) \
            .all()

        done_class_ids = department.classes \
            .filter(instances__enrollments__student__in=user_students, ) \
            .exclude(id__in=current_class_ids) \
            .distinct() \
            .values_list('id', flat=True) \
            .all()

        classes = department.classes \
            .annotate(section_count=djm.Count('synopsis_sections'),
                      exercise_count=djm.Count('synopsis_sections__exercises')) \
            .filter(instances__year__gt=settings.COLLEGE_YEAR - 2) \
            .order_by('name') \
            .all()

        current, done, other = [], [], []
        for class_ in classes:
            if class_.id in current_class_ids:
                current.append(class_)
            elif class_.id in done_class_ids:
                done.append(class_)
            else:
                other.append(class_)

        context['other_classes'] = other
        context['current_classes'] = current
        context['done_classes'] = done
    else:
        context['classes'] = department.classes \
            .annotate(section_count=djm.Count('synopsis_sections'),
                      exercise_count=djm.Count('synopsis_sections__exercises')) \
            .order_by('name') \
            .all()

    context['sub_nav'] = [{'name': 'Exercicios', 'url': reverse('learning:exercises')},
                          {'name': department.name,
                           'url': reverse('learning:department_exercises', args=[department_id])}]
    return render(request, 'learning/department_exercises.html', context)


def questions_view(request):
    context = build_base_context(request)
    context['pcode'] = 'l_questions'
    context['title'] = 'Dúvidas'
    context['recent_objects'] = \
        m.Question.objects \
            .select_related('user') \
            .prefetch_related('linked_classes', 'linked_exercises', 'linked_sections') \
            .order_by('timestamp') \
            .annotate(answer_count=Count('answers')) \
            .reverse()[:50]
    context['popular_objects'] = \
        m.Question.objects \
            .order_by(F('upvotes') + F('downvotes'), 'timestamp') \
            .select_related('user') \
            .annotate(answer_count=Count('answers')) \
            .reverse()[:50]
    if request.user.has_perm('learning.add_question'):
        context['create_url'] = reverse('learning:question_create')
    context['sub_nav'] = [{'name': 'Questões', 'url': reverse('learning:questions')}]
    return render(request, 'supernova/recent_and_popular_lists.html', context)


@login_required
@permission_required('learning.add_question', raise_exception=True)
def question_create_view(request):
    context = build_base_context(request)
    context['pcode'] = 'l_question_create'
    context['title'] = 'Colocar dúvida'
    if request.method == 'POST':
        form = f.QuestionForm(request.POST)
        if form.is_valid():
            with reversion.create_revision():
                question = form.save(commit=False)
                question.user = request.user
                question.save()
                form.save_m2m()
                reversion.set_user(request.user)
            return redirect('learning:question', question_id=question.activity_id)
    else:
        initial = {}
        if 'section' in request.GET:
            try:
                section = m.Section.objects.filter(id=int(request.GET['section'])).first()
                if section is not None:
                    initial['linked_sections'] = [section, ]
            except ValueError:
                pass
        if 'exercise' in request.GET:
            try:
                section = m.Exercise.objects.filter(id=int(request.GET['exercise'])).first()
                if section is not None:
                    initial['linked_exercises'] = [section, ]
            except ValueError:
                pass
        if 'class' in request.GET:
            try:
                klass = college.Class.objects.filter(id=int(request.GET['class'])).first()
                if klass is not None:
                    initial['linked_classes'] = [klass, ]
            except ValueError:
                pass
        form = f.QuestionForm(initial=initial)
    context['form'] = form
    context['sub_nav'] = [{'name': 'Questões', 'url': reverse('learning:questions')},
                          {'name': 'Colocar questão', 'url': reverse('learning:question_create')}]
    return render(request, 'learning/question_editor.html', context)


def question_view(request, question_id):
    question = get_object_or_404(
        m.Question.objects.prefetch_related('answers'),
        activity_id=question_id)
    answer_form = None
    status = 200
    if request.user.is_authenticated:
        if request.method == 'POST':
            if not request.user.has_perm('learning.add_question'):
                context = build_base_context(request)
                context['pcode'] = 'l_question'
                context['title'] = context['msg_title'] = 'Insuficiência de permissões'
                context['msg_content'] = 'O seu utilizador não tem permissões para responder.'
                return render(request, 'supernova/message.html', context, status=403)

            if 'submit' in request.GET and request.GET['submit'] == 'answer':
                answer_form = f.AnswerForm(request.POST)
                if answer_form.is_valid():
                    with reversion.create_revision():
                        answer = answer_form.save(commit=False)
                        answer.to = question
                        answer.user = request.user
                        answer.save()
                        # Reload data, new form
                        question.refresh_from_db()
                        reversion.set_user(request.user)
                    m.AnswerNotification.objects.create(receiver=question.user, answer=answer)
                    return HttpResponseRedirect(answer.get_absolute_url())
            else:
                status = 400
        else:
            answer_form = f.AnswerForm()

    context = build_base_context(request)
    context['pcode'] = 'l_question'
    context['title'] = 'Dúvida: %s' % question.title
    context['question'] = question
    context['answer_form'] = answer_form
    context['sub_nav'] = [{'name': 'Questões', 'url': reverse('learning:questions')},
                          {'name': question.title, 'url': reverse('learning:question', args=[question_id])}]
    return render(request, 'learning/question.html', context, status=status)


@login_required
@permission_required('learning.add_question', raise_exception=True)
def question_edit_view(request, question_id):
    question = get_object_or_404(
        m.Question.objects,
        activity_id=question_id)
    context = build_base_context(request)
    context['pcode'] = 'l_question_edit'
    context['title'] = f'Editar "{question.title}"'
    if request.method == 'POST':
        form = f.QuestionForm(request.POST, instance=question)
        if form.is_valid():
            with reversion.create_revision():
                form.save()
                reversion.set_user(request.user)
            return redirect('learning:question', question_id=question.activity_id)
    else:
        form = f.QuestionForm(instance=question)

    context['form'] = form

    versions = Version.objects \
        .select_related('revision__user') \
        .order_by('revision__date_created') \
        .get_for_object(question)

    changes = []
    for i in range(len(versions) - 1):
        v_from = versions[i]
        v_to = versions[i + 1]
        content_from = v_from.field_dict['content']
        content_to = v_to.field_dict['content']
        if content_from == content_to:
            content_diff = None
        else:
            content_diff = comparison_html(v_from.field_dict['content'], v_to.field_dict['content'])
        changes.append(
            (v_to.revision.user,
             v_to.revision.date_created,
             content_diff))
    if len(changes) > 0:
        context['changes'] = changes
    context['sub_nav'] = [{'name': 'Questões', 'url': reverse('learning:questions')},
                          {'name': question.title, 'url': reverse('learning:question', args=[question_id])},
                          {'name': 'Editar', 'url': reverse('learning:question_edit', args=[question.activity_id])}]
    return render(request, 'learning/question_editor.html', context)


@login_required
@permission_required('learning.add_answer', raise_exception=True)
def answer_edit_view(request, answer_id):
    answer = get_object_or_404(
        m.Answer.objects,
        activity_id=answer_id)
    context = build_base_context(request)
    context['pcode'] = 'l_answer_edit'
    context['title'] = 'Editar resposta'
    if request.method == 'POST':
        form = f.AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            with reversion.create_revision():
                answer = form.save()
                reversion.set_user(request.user)
            return redirect('learning:question', question_id=answer.to.activity_id)
    else:
        form = f.AnswerForm(instance=answer)

    context['form'] = form

    versions = Version.objects \
        .select_related('revision__user') \
        .order_by('revision__date_created') \
        .get_for_object(answer)

    changes = []
    for i in range(len(versions) - 1):
        v_from = versions[i]
        v_to = versions[i + 1]
        changes.append(
            (v_to.revision.user,
             v_to.revision.date_created,
             comparison_html(v_from.field_dict['content'], v_to.field_dict['content'])))
    if len(changes) > 0:
        context['changes'] = changes
    context['sub_nav'] = [{'name': 'Questões', 'url': reverse('learning:questions')},
                          {'name': answer.to.title, 'url': reverse('learning:question', args=[answer.to.activity_id])},
                          {'name': 'Editar resposta',
                           'url': reverse('learning:answer_edit', args=[answer.activity_id])}]
    return render(request, 'learning/answer_editor.html', context)


def exercise_preview_view(request):
    if request.method == 'POST':
        context = build_base_context(request)
        if 'content' in request.POST:
            html = m.Exercise(content=json.loads(request.POST['content'])).render_html
            context['content'] = html
            return render(request, 'supernova/base_minimal.html', context)
        return HttpResponse(status=400)
    else:
        return Http404()


class AreaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = m.Area.objects.all()
        if self.q:
            try:
                qs = qs.filter(Q(id=int(self.q)) | Q(title__istartswith=self.q))
            except ValueError:
                qs = qs.filter(title__contains=self.q)
        return qs


class SubareaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = m.Subarea.objects.all()
        if self.q:
            try:
                qs = qs.filter(Q(id=int(self.q)) | Q(title__istartswith=self.q))
            except ValueError:
                qs = qs.filter(title__contains=self.q)
        return qs


class SectionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = m.Section.objects.all()
        if self.q:
            try:
                qs = qs.filter(Q(id=int(self.q)) | Q(title__contains=self.q))
            except ValueError:
                qs = qs.filter(title__contains=self.q)
        return qs


class ExerciseAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = m.Exercise.objects.all()
        if self.q:
            try:
                qs = qs.filter(id=int(self.q))
            except ValueError:
                qs = None
        return qs
