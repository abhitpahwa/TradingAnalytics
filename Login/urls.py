from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

from django.conf.urls import url
import re
app_name="login"

urlpatterns=[
    path('',views.IndexView),
    path('home/',views.HomeView),
    path('weeks/',views.Weeks.as_view()),
    path('adminlogin/',views.AdminView),
    path('report/',views.ReportView),
    path('mylimits/',views.MyLimits),
    path('requeststatus/',views.RequestHistory),
    path('mentor/',views.MentorView,name="mentor"),
    path('risk/',views.RiskView),
    path('support/',views.Support),
    url(r'^calendar/$', views.CalendarView.as_view(), name='calendar'),
    path('logout/',views.logout)
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)

