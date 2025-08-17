from django.db import models
from employee.models import *
APPROVAL_CHOICES = [
    ('approved', 'approved'),
    ('pending', 'pending'),
    ('declined', 'declined'),
]
# Create your models here.
class LeaveApplications(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaveApplicationsEmployee')
    dutyHandOver = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaveApplicationsHandOver')
    leaveType = models.CharField(max_length=50)
    applyDate = models.DateTimeField(auto_now_add=True)
    startDate = models.DateField()
    endDate = models.DateField()
    reason = models.TextField()
    deptApproval = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    deptApprovedBy = models.ForeignKey(
        Employee, on_delete=models.PROTECT,
        related_name='dept_approved_leave',
        null=True, blank=True
    )

    HRApproval = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    HRApprovedBy = models.ForeignKey(
        Employee, on_delete=models.PROTECT,
        related_name='HR_approved_leave',
        null=True, blank=True
    )

    finalApproval = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    finalApprovedBy = models.ForeignKey(
        Employee, on_delete=models.PROTECT,
        related_name='final_approved_leave',
        null=True, blank=True
    )

    remarks = models.CharField(max_length=100, default='')

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.leaveType} ({self.startDate} to {self.endDate})"
    



# Create your models here.
class VisitApplications(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='visitApplicationsEmployee')
    applyDate = models.DateTimeField(auto_now_add=True)
    startDate = models.DateField()
    endDate = models.DateField()
    visitTo = models.CharField(max_length=100)
    reason = models.TextField()
    deptApproval = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    deptApprovedBy = models.ForeignKey(
        Employee, on_delete=models.PROTECT,
        related_name='dept_approved_visit',
        null=True, blank=True
    )

    HRApproval = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    HRApprovedBy = models.ForeignKey(
        Employee, on_delete=models.PROTECT,
        related_name='HR_approved_visit',
        null=True, blank=True
    )

    finalApproval = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    finalApprovedBy = models.ForeignKey(
        Employee, on_delete=models.PROTECT,
        related_name='final_approved_visit',
        null=True, blank=True
    )

    remarks = models.CharField(max_length=100, default='')
    photo = models.ImageField(upload_to="attendance_photos/", null=True, blank=True)
    latitude = models.CharField(default='', null=True, blank=True, max_length=100)
    longitude = models.CharField(default='', null=True, blank=True, max_length=100)


    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.visitTo} ({self.startDate} to {self.endDate})"