from django.urls import path

from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('nucleos', views.nuclei_view, name='nuclei'),
    path('institucionais', views.institutional_view, name='institutional'),
    path('pedagogicos', views.pedagogic_view, name='pedagogic'),
    path('comunidades', views.communities_view, name='communities'),
    path('<str:group_abbr>', views.group_view, name='group'),
    path('<str:group_abbr>/documentos', views.documents_view, name='documents'),
    path('<str:group_abbr>/anuncios', views.announcements_view, name='announcements'),
    path('<str:group_abbr>/membros', views.members_view, name='members'),
    path('<str:group_abbr>/admissao', views.group_membership_request_view, name='membership_req'),
    path('<str:group_abbr>/candidaturas', views.group_candidates_view, name='candidates'),
    path('<str:group_abbr>/definicoes', views.settings_view, name='settings'),
    path('<str:group_abbr>/cargos', views.roles_view, name='roles'),
    path('<str:group_abbr>/cargo/<int:role_id>', views.role_view, name='role'),
    path('<str:group_abbr>/anunciar', views.announce_view, name='announce'),
    path('<str:group_abbr>/anuncio/<str:announcement_id>', views.announcement_view, name='announcement'),
    path('<str:group_abbr>/agendar', views.calendar_management_view, name='calendar_manage'),
    path('<str:group_abbr>/conversas', views.conversations_view, name='conversations'),
    path('<str:group_abbr>/conversas/criar', views.conversation_create_view, name='conversation_create'),
    path('<str:group_abbr>/conversas/<str:conversation_id>', views.conversation_view, name='conversation'),
    path('ac/group_role', views.GroupRolesAutocomplete.as_view(), name='group_role_ac'),
]
