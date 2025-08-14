from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Designation(models.Model):
    title = models.CharField(max_length=100)
    level = models.IntegerField(default=1)
    def __str__(self):
        return self.title


class Employee(models.Model):
    fingerPrintID = models.IntegerField(unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees')
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, related_name='employees')
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    join_date = models.DateField(auto_now_add=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    profile_picture = models.ImageField(upload_to='employee_photos/', null=True, blank=True)
    status = models.CharField(max_length=100)
    password = models.CharField(max_length=100, default='')
    casualLeave = models.IntegerField(default=10)
    medicalLeave = models.IntegerField(default=10)
    annualLeave = models.IntegerField(default=15)
    otherLeave = models.IntegerField(default=10)
    

    def __str__(self):
        try:
            return f"{self.user.get_full_name()} - {self.department.name} - {self.designation.title} ({self.designation.level})"
        except:
            return f"{self.user.get_full_name()}"
    

class Award(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='awards')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date_awarded = models.DateField()
    amount = models.FloatField()

    def __str__(self):
        return f"{self.title} - {self.employee.user.get_full_name()}"
    

class HealthInsurance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='health_insurances')
    coverage_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.employee.user.get_full_name()}"


class Car(models.Model):
    carModel = models.CharField(max_length=100)
    number = models.CharField(max_length=100)
    inclusionDate = models.CharField(max_length=100)
    fuelReimbursement = models.FloatField()

    def __str__(self):
        return self.carModel + "___" + self.number
    
class Mobile(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='mobiles')
    mobileModel = models.CharField(max_length=15)
    allocationDate = models.DateField(auto_now_add=True)
    amount = models.FloatField()
    file = models.FileField(upload_to='mobile_reimbursement')


    # def __str__(self):
    #     return f"{self.mobile_number} - {self.employee.user.get_full_name()}"
    
class Accomodation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='accomodations')
    reimbursement = models.CharField(max_length=15)
    allocationDate = models.DateField(auto_now_add=True)
    file = models.FileField(upload_to='accomodation_reimbursement')

    def __str__(self):
        return f"{self.allocationDate} - {self.employee.user.get_full_name()}"
    

class TravelAllowance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='travelAllowance')
    amount = models.CharField(max_length=15)
    allocationDate = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.allocationDate} - {self.employee.user.get_full_name()}"
    

class CarUsage(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='car_usages')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='car_usages')
    usage_date = models.DateField()
    startTime = models.TimeField()
    endTime = models.TimeField()
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    distance_covered = models.FloatField()
    purpose = models.TextField()

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.car.carModel} on {self.usage_date}"
    


class LunchEnrollment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    enrolled_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - Lunch"
    








APPROVAL_CHOICES = [
    ('approved', 'Approved'),
    ('pending', 'Pending'),
    ('declined', 'Declined'),
]

class Reimbursements(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reimbursements')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField()
    dateRequested = models.DateField(auto_now_add=True)

    deptApproval = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    deptApprovedBy = models.ForeignKey(
        Employee, on_delete=models.PROTECT,
        related_name='dept_approved_reimbursements',
        null=True, blank=True
    )

    commercialApproval = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    commercialApprovedBy = models.ForeignKey(
        Employee, on_delete=models.PROTECT,
        related_name='commercial_approved_reimbursements',
        null=True, blank=True
    )

    finalApproval = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    finalApprovedBy = models.ForeignKey(
        Employee, on_delete=models.PROTECT,
        related_name='final_approved_reimbursements',
        null=True, blank=True
    )
    moneyRecieved = models.BooleanField(default=False)
    reason = models.CharField(max_length=100)
    purchasedFrom = models.CharField(max_length=100)
    file = models.FileField(upload_to='reimbursement_files', null=True, blank=True)
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.amount} BDT on {self.dateRequested}"
