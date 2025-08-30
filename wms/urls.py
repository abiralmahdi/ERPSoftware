from django.urls import path
from . import views

urlpatterns = [
    path('projects', views.projects, name='projects'),
    path('projects/<int:projectID>', views.indivProject, name='indivProject'),
    path('projects/<int:projectID>/tasks', views.projectTasks, name='projectTasks'),
    path('projects/<int:projectID>/tasks/<int:taskID>/delete', views.deleteTask, name='delete_task'),
    path('projects/<int:project_id>/tasks/<int:task_id>/viewHistory/', views.view_task_history, name='view_task_history'),
    path('projects/<int:projectID>/board', views.board, name='board'),
    path('projects/<int:projectID>/timeline', views.timeline, name='timeline'),
    path('projects/<int:projectID>/calendar', views.calendar_view, name='calendar'),

]