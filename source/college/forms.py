import re
from itertools import chain

from dal import autocomplete
from django import forms as djf
from college import models as m
from supernova.widgets import FCTMapWidget

IDENTIFIER_EXP = re.compile('(?!^\d+$)^[\da-zA-Z-_.]+$')


class Loggable(djf.ModelForm):
    def get_changes(self):
        changes = {'attrs': self.changed_data}
        old, new = dict(), dict()
        for changed_attr in (attr for attr in self.Meta.loggable_fields if attr in self.changed_data):
            old[changed_attr] = self.initial[changed_attr]
            new[changed_attr] = self.cleaned_data[changed_attr]
        changes['old'] = old
        changes['new'] = new
        return changes


class CourseForm(Loggable, djf.ModelForm):
    class Meta:
        model = m.Course
        fields = ('description', 'department', 'url', 'coordinator')
        loggable_fields = ('description', 'department', 'url')


class DepartmentForm(Loggable, djf.ModelForm):
    class Meta:
        model = m.Department
        fields = ('description', 'building', 'picture', 'url', 'email', 'phone', 'president')
        loggable_fields = ('description', 'phone', 'url', 'email')


class ClassForm(Loggable, djf.ModelForm):
    class Meta:
        model = m.Class
        fields = ('description', 'url')
        loggable_fields = ('description', 'url')


class TeacherForm(Loggable, djf.ModelForm):
    class Meta:
        model = m.Teacher
        fields = ('picture', 'url', 'email', 'phone', 'rank')
        loggable_fields = ('url', 'email', 'phone')


class ClassInstanceForm(Loggable, djf.ModelForm):
    class Meta:
        model = m.ClassInstance
        fields = ('regent', 'visibility')
        loggable_fields = ('availability',)


class ClassFileForm(Loggable, djf.ModelForm):
    class Meta:
        model = m.ClassFile
        fields = ('name', 'category', 'visibility')
        loggable_fields = ('name', 'type', 'visibility')


class ClassFileCompleteForm(Loggable, djf.ModelForm):
    class Meta:
        model = m.ClassFile
        fields = ('file', 'name', 'category', 'visibility')
        loggable_fields = ('name', 'type', 'visibility')
        widgets = {
            'file': autocomplete.ModelSelect2(url='college:file_ac')
        }


class FileForm(Loggable, djf.ModelForm):
    class Meta:
        model = m.File
        fields = ('license', 'authors', 'author_str', 'doi')
        loggable_fields = ('author_str', 'doi')
        widgets = {
            'authors': autocomplete.ModelSelect2Multiple(url='users:nickname_ac')
        }


class FileUploadForm(djf.ModelForm):
    file = djf.FileField()

    class Meta:
        model = m.File
        fields = ('license', 'authors', 'author_str', 'doi')
        widgets = {
            'authors': autocomplete.ModelSelect2Multiple(url='users:nickname_ac')
        }


class RoomForm(Loggable, djf.ModelForm):
    class Meta:
        model = m.Room
        fields = ('name', 'floor', 'unlocked', 'location',
                  'features', 'department', 'capacity', 'door_number',
                  'type', 'description', 'equipment')
        loggable_fields = ('name', 'type', 'visibility')
        widgets = {
            'location': FCTMapWidget(),
            'department': autocomplete.Select2(),
            'features': autocomplete.Select2Multiple(),
        }


ClassFileFormset = djf.inlineformset_factory(
    m.ClassInstance,
    m.ClassFile,
    form=ClassFileForm,
    can_delete=False,
    extra=0)


def merge_changes(old_changes, new_changes):
    original = old_changes['old']
    # intermediary = old_changes['new']
    future = new_changes['new']
    attrs = list(set(chain(old_changes['attrs'], new_changes['attrs'])))
    # Check for reverted changes
    for attr in original.keys():
        if attr in future and original[attr] == future[attr]:
            attrs.remove(attr)
            future.pop(original, None)
            future.pop(attr, None)
    return {
        'old': original,
        'new': original,
        'attrs': attrs
    }


class CurriculumClassComponentForm(djf.ModelForm):
    class Meta:
        model = m.CurricularClassComponent
        fields = ('__all__')
        widgets = {
            'klass': autocomplete.Select2(url='college:class_ac'),
        }


class CurriculumBlockComponentForm(djf.ModelForm):
    class Meta:
        model = m.CurricularBlockComponent
        fields = ('__all__')
        widgets = {
            'children': autocomplete.Select2Multiple(url='college:curr_component_ac'),
        }


class CurriculumBlockVariantComponentForm(djf.ModelForm):
    class Meta:
        model = m.CurricularBlockVariantComponent
        fields = ('__all__')
        widgets = {
            'children': autocomplete.Select2Multiple(url='college:curr_block_ac'),
        }
