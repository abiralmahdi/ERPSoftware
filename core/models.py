from django.db import models

# Create your models here.
class GlobalConfig(models.Model):
    casualLeave = models.IntegerField()
    medicallLeave = models.IntegerField()
    annualLeave = models.IntegerField()
    otherLeave = models.IntegerField()
    leaveNotification = models.BooleanField(default=False)
    visitNotification = models.BooleanField(default=False)
    