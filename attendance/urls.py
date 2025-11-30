from django.urls import path
from . import views

urlpatterns = [
    path('attendanceList', views.attendanceList, name='attendanceList'),
    path('scanAttendance', views.scanAttendance, name='scanAttendance'),
    path('remoteAttendance', views.remoteAttendance, name='remoteAttendance'),
    path("submitAttendance", views.submitAttendance, name="submitAttendance"),
    path("outTime/<str:attendanceID>", views.outTime, name="outTime"),
    path('attendanceDashboard', views.attendanceDashboard, name='attendanceDashboard'),
    path("get-absentees/", views.get_absentees, name="get_absentees"),
    path("attendance-data/", views.attendance_chart_data, name="attendance_chart_data"),
    path("get-quickview/", views.get_quickview, name="get_quickview"),
    path("attendance_pie_chart/<str:employee_id>", views.attendance_pie_chart, name="attendance_pie_chart"),
    path("employee_monthly_attendance/<str:employee_id>", views.employee_monthly_attendance, name="employee_monthly_attendance"),
    path("calendar", views.calendar_view, name="calendar_view"),
    path("calendar/add_holiday/", views.add_holiday, name="add_holiday"),
    path("getLocation", views.getLocation, name="getLocation"),
    path("sendLocation", views.sendLocation, name="sendLocation"),
    path("seeEmployeeLocation", views.seeEmployeeLocation, name="seeEmployeeLocation"),
    path("getLocation/<str:employeeID>", views.getLocation2, name="getLocation2"),
    path('api/login/', views.api_login, name="api_login"),
]


    