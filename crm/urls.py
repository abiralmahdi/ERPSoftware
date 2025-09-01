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
    path('offers/generatePDF', views.generatePDF, name='generatePDF'),
    path('addOffer/<str:leadID>', views.addOffer, name='addOffer'),
    path('editOffer/<str:offerID>', views.editOffer, name='editOffer'),
    path('orders', views.orders, name='orders'),
    path('addOrder/<str:offerID>', views.addOrder, name='addOrder'),
    path('editOrder/<str:order_id>', views.editOrder, name='editOrder'),
    path('sales', views.sales, name='sales'),
    path('editSale/<str:saleID>', views.editSale, name='editSale'),
    path('accountsRecieveable', views.accountsRecieveable, name='accountsRecieveable'),
    path('updateAccountsRecievable/<str:pk>', views.updateAccountsRecieveable, name='updateAccountsRecieveable'),
    path('employeeWeeklyStatus/<str:employee_id>', views.employeeWeeklyStatus, name='employeeWeeklyStatus'),
]