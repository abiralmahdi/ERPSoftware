from django.db import models
from employee.models import *

# Create your models here.
class Projects(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    startDate = models.DateField()
    endDate = models.DateField()
    status = models.CharField(max_length=50)
    createdAt = models.DateTimeField(auto_now_add=True)
    projectLeader = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, null=True, blank=True)

class Task(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    assignedTo = models.ForeignKey(Employee, on_delete=models.DO_NOTHING)
    assignTime = models.DateTimeField()
    deadline = models.DateTimeField()
    status = models.CharField(max_length=50)
    priority = models.CharField(max_length=50)
    description = models.TextField()
    createdBy = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, related_name='created_by')
    progress = models.FloatField(default=0)

class TaskHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    name = models.CharField(max_length=100)
    assignedTo = models.ForeignKey(Employee, on_delete=models.DO_NOTHING)
    assignTime = models.DateTimeField()
    deadline = models.DateTimeField()
    status = models.CharField(max_length=50)
    priority = models.CharField(max_length=50)
    description = models.TextField()
    progress = models.FloatField(default=0)
    edited_at = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, related_name='edited_tasks')
