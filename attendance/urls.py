from django.urls import path
from . import views

urlpatterns = [
    path('attendanceList', views.attendanceList, name='attendanceList'),
    path('remoteAttendance', views.remoteAttendance, name='remoteAttendance'),
    path("submitAttendance", views.submitAttendance, name="submitAttendance"),
    path("outTime/<str:attendanceID>", views.outTime, name="outTime"),
    path('attendanceDashboard', views.attendanceDashboard, name='attendanceDashboard'),
    path("get-absentees/", views.get_absentees, name="get_absentees"),
    path("attendance-data/", views.attendance_chart_data, name="attendance_chart_data"),
    path("get-quickview/", views.get_quickview, name="get_quickview"),
]