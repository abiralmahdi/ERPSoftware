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
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    agent = models.ForeignKey(CustomerAgent, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    visit_application = models.ForeignKey(VisitApplications, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=100)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    note = models.CharField(max_length=100)
    potentialScope = models.CharField(max_length=100)


    def __str__(self):
        return f"Visit to {self.customer.name} on {self.startDate}"
    

class Lead(models.Model):
    customerVisit = models.ForeignKey(CustomerVisits, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    scopeOfSupply = models.CharField(max_length=100)
    status = models.CharField(max_length=10)


    class Meta:
        unique_together = ('customerVisit', 'date')

    def __str__(self):
        return f"Lead for {self.customer.name} by {self.agent.agent_name} on {self.lead_date}"
    

class Offer(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    offer_date = models.DateField(auto_now_add=True)
    offer_details = models.CharField(max_length=100)
    status = models.CharField(max_length=10)

    class Meta:
        unique_together = ('lead', 'offer_date')

    def __str__(self):
        return f"Offer for {self.lead.customerVisit.customer.name} on {self.offer_date}"