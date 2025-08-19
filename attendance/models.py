from django.db import models
from employee.models import *

# Create your models here.
class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    date = models.DateField(auto_now_add=False)
    inTime = models.TimeField(auto_now_add=False, null=True, blank=True)
    outTime = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
    ], default='present')
    remote = models.BooleanField(default=False)
    reason = models.TextField(null=True, blank=True, default="")
    location = models.CharField(max_length=100, null=True, blank=True, default="")
    longitude = models.CharField(max_length=100, null=True, blank=True, default="")
    latitude = models.CharField(max_length=100, null=True, blank=True, default="")
    photo = models.ImageField(upload_to="attendance_photos/", null=True, blank=True)


class Holiday(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.date} - {self.name}"