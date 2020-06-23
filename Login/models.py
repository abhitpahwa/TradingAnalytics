from django.db import models
# Create your models here.

class Report(models.Model):
    report_file=models.TextField()
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Trader(models.Model):
    account=models.CharField(max_length=50)
    email=models.EmailField()
    def __str__(self):
        return self.email
