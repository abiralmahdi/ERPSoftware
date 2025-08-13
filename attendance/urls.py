from django.urls import path
from . import views

urlpatterns = [
    path('attendanceList', views.attendanceList, name='attendanceList'),
    path('attendanceDashboard', views.attendanceDashboard, name='attendanceDashboard'),
    path("get-absentees/", views.get_absentees, name="get_absentees"),
    path("attendance-data/", views.attendance_chart_data, name="attendance_chart_data"),
]