from django.contrib import admin

from . import models

# Register your models here.
admin.site.register(models.Report)
admin.site.register(models.Trader)
admin.site.register(models.Request_Trader_Mapping)
admin.site.register(models.Request)
admin.site.register(models.SupportDb)
admin.site.register(models.Event)