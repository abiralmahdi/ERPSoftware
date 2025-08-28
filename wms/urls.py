from django.urls import path
from . import views

urlpatterns = [
    path('projects', views.projects, name='projects'),
    path('projects/<int:projectID>', views.indivProject, name='indivProject'),
    path('projects/<int:projectID>/tasks', views.projectTasks, name='projectTasks'),
    path('projects/<int:projectID>/board', views.board, name='board'),
    path('projects/<int:projectID>/timeline', views.timeline, name='timeline'),

]