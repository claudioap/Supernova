from django.urls import path

from . import views

app_name = 'college'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('campus/', views.map_view, name='campus'),
    path('campus/mapa/', views.map_view, name='map'),
    path('campus/transportes/', views.transportation_view, name='transportation'),
    path('campus/disponivel/', views.available_places_view, name='available_places'),
    path('campus/edificios/', views.buildings_view, name='buildings'),
    path('campus/edificio/<int:building_id>/', views.building_view, name='building'),
    path('departamentos/', views.departments_view, name='departments'),
    path('departamento/<int:department_id>/', views.department_view, name='department'),
    path('departamento/<int:department_id>/editar', views.department_edit_view, name='department_edit'),
    path('professor/<int:teacher_id>', views.teacher_view, name='teacher'),
    path('professor/<int:teacher_id>/editar', views.teacher_edit_view, name='teacher_edit'),
    path('cadeira/<int:class_id>/', views.class_view, name='class'),
    path('cadeira/<int:class_id>/editar', views.class_edit_view, name='class_edit'),
    path('cadeira/i/<int:instance_id>/', views.class_instance_view, name='class_instance'),
    path('cadeira/i/<int:instance_id>/turnos', views.class_instance_shifts_view, name='class_instance_shifts'),
    path('cadeira/i/<int:instance_id>/inscritos', views.class_instance_enrolled_view, name='class_instance_enrolled'),
    path('cadeira/i/<int:instance_id>/ficheiros', views.class_instance_files_view, name='class_instance_files'),
    path('cadeira/i/<int:instance_id>/ficheiro/<str:file_hash>', views.class_instance_file_download, name='class_instance_file_download'),
    path('sala/<int:room_id>/', views.room_view, name='room'),
    path('cursos/', views.courses_view, name='courses'),
    path('curso/<int:course_id>/', views.course_view, name='course'),
    path('curso/<int:course_id>/alunos/', views.course_students_view, name='course_students'),
    path('curso/<int:course_id>/programa/', views.course_curriculum_view, name='course_curriculum'),
    path('curso/<int:course_id>/editar', views.course_edit_view, name='course_edit'),
    path('ac/class', views.ClassAutocomplete.as_view(), name='class_ac'),
    path('ac/place', views.PlaceAutocomplete.as_view(), name='place_ac'),
]
