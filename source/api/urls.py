from django.urls import path

from api import views

urlpatterns = [
    # College
    path('buildings/', views.college.BuildingList.as_view()),
    path('building/<int:pk>/', views.college.BuildingDetailed.as_view()),
    path('departments/', views.college.DepartmentList.as_view()),
    path('department/<int:pk>/', views.college.DepartmentDetailed.as_view()),
    path('course/<int:pk>/', views.college.CourseDetailed.as_view()),
    path('class/<int:pk>/', views.college.ClassDetailed.as_view()),
    # Groups
    path('groups/', views.groups.GroupList.as_view()),
    # News
    path('news/', views.news.NewsList.as_view()),
    path('news/<int:pk>/', views.news.News.as_view()),
    # Services
    path('services/', views.services.ServiceList.as_view()),
    path('bars/', views.services.BarList.as_view()),
    path('transportation/next', views.third_party.transportation_upcoming, name="transportation_upcoming"),
    path('weather/', views.third_party.weather),
    path('weather/chart/', views.third_party.weather_chart),
    path('boinc/users/', views.third_party.boinc_users),
    path('boinc/projects/', views.third_party.boinc_projects),
    path('stars/gitlab/', views.third_party.gitlab_stars),
    path('stars/github/', views.third_party.github_stars),
    # Store
    path('store/', views.store.Store.as_view()),
    # Synopses
    path('synopses/areas/', views.synopses.Areas.as_view()),
    path('synopses/area/<int:pk>/', views.synopses.Area.as_view()),
    path('synopses/subarea/<int:pk>/', views.synopses.Subarea.as_view()),
    path('synopses/topic/<int:pk>/', views.synopses.TopicSections.as_view()),
    path('synopses/class/<int:pk>/', views.synopses.ClassSections.as_view()),
    path('synopses/section/<int:pk>/', views.synopses.Section.as_view()),
    # Users
    path('profile/<str:nickname>/', views.users.ProfileDetailed.as_view()),
    path('profile/<str:nickname>/socialnetworks/', views.users.UserSocialNetworks.as_view(), name='social_networks'),
]
