from django.urls import path

from . import views

app_name="login"

urlpatterns=[
    path('',views.IndexView),
    path('weeks/',views.Weeks.as_view()),
    path('adminlogin/',views.AdminView),
    path('report/',views.ReportView)
]

