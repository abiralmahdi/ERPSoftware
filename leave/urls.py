from django.urls import path
from . import views

urlpatterns = [
    path('leaveApplications', views.leaveApplications, name='leaveApplications'),
    path('approveLeaveApplication/<str:applicationID>', views.approveLeave, name='approveLeave'),
    path('declineLeaveApplication/<str:applicationID>', views.declineLeave, name='declineLeave'),
    path('leaveAdjustment', views.leaveAdjustment, name='leaveAdjustment'),
    path('updateLeaveAdjustment/<str:employeeID>', views.updateLeaveAdjustment, name='updateLeaveAdjustment'),
    path('visitApplications', views.visitApplications, name='visitApplications'),
    path('approveVisitApplication/<str:applicationID>', views.approveVisit, name='approveVisit'),
    path('declineVisitApplication/<str:applicationID>', views.declineVisit, name='declineVisit'),
    path('dashboard', views.leaveDashboard, name='leaveDashboard'),
    path('dashboard-data/<int:year>/', views.leaveDashboardData, name='leaveDashboardData'),
]