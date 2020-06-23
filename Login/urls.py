from django.urls import path
from django.urls import include
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name="login"

urlpatterns=[
    path('',views.IndexView),
    path('weeks/',views.Weeks.as_view()),
    path('adminlogin/',views.AdminView),
    path('report/',views.ReportView)
]

