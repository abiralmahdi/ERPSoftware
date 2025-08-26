from django.db import models
from leave.models import VisitApplications
from employee.models import Employee

# Create your models here.
class Customer(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)

class CustomerAgent(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='agent')
    agent_name = models.CharField(max_length=100)
    agent_email = models.CharField(max_length=100)
    agent_contact = models.CharField(max_length=100)

    class Meta:
        unique_together = ('customer', 'agent_email')

    def __str__(self):
        return f"{self.agent_name} ({self.agent_email}) for {self.customer.name}"
    
class CustomerVisits(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(CustomerAgent, on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    visit_application = models.ForeignKey(VisitApplications, on_delete=models.CASCADE, null=True, blank=True)
    purpose = models.CharField(max_length=100, null=True, blank=True)
    startDate = models.DateTimeField(null=True, blank=True)
    endDate = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=100, null=True, blank=True)
    potentialScope = models.CharField(max_length=100, null=True, blank=True)
    scopeFile = models.FileField(upload_to='files')


    def __str__(self):
        return f"Visit to {self.customer.name} on {self.startDate}"
    

class Lead(models.Model):
    customerVisit = models.ForeignKey(CustomerVisits, on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='leadGeneratedBy')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(CustomerAgent, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    scopeOfSupply = models.CharField(max_length=100, null=True, blank=True)
    scopeFile = models.FileField(upload_to='files', null=True, blank=True)
    note = models.CharField(max_length=100, default='', null=True, blank=True)
    status = models.CharField(max_length=10, null=True, blank=True)
    offerSubmissionDate = models.DateField(null=True, blank=True)
    assignedTo = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='leadAssignedTo')

    
from datetime import date
class Offer(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='offer')
    offer_date = models.DateField(null=True, blank=True)
    negoDate = models.DateField(null=True, blank=True)
    tgtPrice = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    offerValue = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, null=True, blank=True)
    note = models.CharField(max_length=100, null=True, blank=True)
    offerFile = models.FileField(upload_to='files', null=True, blank=True)


class Order(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='order')
    delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    order_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    poRef = models.CharField(max_length=100, null=True, blank=True, default='')
    note = models.CharField(max_length=100, null=True, blank=True)


class OrderFiles(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='orderFile')
    file = models.FileField(upload_to='orderfiles', null=True, blank=True)

class Sales(models.Model):
    saleOrderReference = models.CharField(max_length=100, default='', null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sales')
    invoiceDate = models.DateField(null=True, blank=True)
    invoiceRef = models.CharField(max_length=100, null=True, blank=True)
    totalInvoiceValue = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ait = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    remarks = models.CharField(max_length=100, null=True, blank=True)

class AccountsRecieveable(models.Model):
    sales = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name='accountsRecieveable')
    invoiceRef = models.CharField(max_length=100, null=True, blank=True)
    paymentDate = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    remarks = models.CharField(max_length=100, null=True, blank=True)
    totalInvoiceValue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
