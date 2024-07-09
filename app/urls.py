from django.urls import path

from . import views

urlpatterns = [
   path('', views.feed, name='feed'),
   path('projects', views.projects, name='projects'),
   path('settings', views.settings, name='settings'),
   path('team', views.team, name='team'),
   path('project', views.create_project, name='create_project'),
   path('projects/delete', views.delete_project, name='delete_project'),
   path('projects/pause', views.pause_project, name='pause_project'),
   path('api/v1/search', views.search.as_view(), name='api_search' ),
   path('api/v1/query_parser', views.query_parser.as_view(), name='query_parser'),
   path('api/tz', views.update_user_timezone.as_view(), name='update_tz'),
   path('api/key_index', views.key_aggergation.as_view(), name='key_agg'),
   path('auth/login/', views.LoginUser, name='login'),
   path('logout/', views.Logout, name='logout'),

]