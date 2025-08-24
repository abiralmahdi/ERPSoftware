from django.urls import path
from . import views

urlpatterns = [
    path('customerVisitPlan', views.customerVisitPlan, name='customerVisitPlan'),
    path('customerList', views.customerList, name='customerList'),
    path('addCustomer', views.addCustomer, name='addCustomer'),
    path('addCustomerVisit', views.addCustomerVisit, name='addCustomerVisit'),
    path('completeVisit/<str:visitID>', views.completeVisit, name='completeVisit'),
    path('addContactPerson', views.addContactPerson, name='addContactPerson'),
    path('lead', views.lead, name='lead'),
    path('addLead/<str:visit_id>', views.addLead, name='addLead'),
    path('addLeadSeperately', views.addLeadSeperately, name='addLeadSeperately'),
    path('completeLead/<str:leadID>', views.completeLead, name='completeLead'),
    path('offers', views.offer, name='offer'),
    path('addOffer/<str:leadID>', views.addOffer, name='addOffer'),
    path('editOffer/<str:offerID>', views.editOffer, name='editOffer'),
]