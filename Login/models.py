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
    mentor=models.EmailField(null=True)
    def __str__(self):
        return self.email

class Request_Trader_Mapping(models.Model):
    request_id=models.CharField(max_length=50,primary_key=True)
    account = models.CharField(max_length=50,null=True)
    email = models.EmailField(null=True)
    mentor_approval=models.CharField(max_length=8,default="Pending")
    risk_approval=models.CharField(max_length=8,default="Pending")
    def __str__(self):
        return self.request_id

class Request(models.Model):
    request_id=models.ForeignKey(Request_Trader_Mapping,on_delete=models.CASCADE)
    trading_software=models.CharField(max_length=50,null=True)
    product=models.CharField(max_length=50,null=True)
    product_type=models.CharField(max_length=50,null=True)
    requested_limit=models.IntegerField(null=True)
    requested_clip=models.IntegerField(null=True)
    def __str__(self):
        return self.request_id.__str__()

class SupportDb(models.Model):
    email=models.EmailField()
    ticket_id=models.CharField(max_length=50,primary_key=True)
    subject=models.CharField(max_length=100)
    body=models.TextField()
    screenshot=models.ImageField(upload_to='screenshots/')

class Event(models.Model):
    product = models.CharField(max_length=200)
    expiry = models.DateTimeField()

