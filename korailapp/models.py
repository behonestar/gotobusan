from django.db import models

class ReserveQueue(models.Model):
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    train_type = models.CharField(max_length=32)
    dep = models.CharField(max_length=32)
    arr = models.CharField(max_length=32)
    date = models.CharField(max_length=32)
    time = models.CharField(max_length=32)
    reserve_code = models.CharField(max_length=32, null=True)