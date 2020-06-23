import codecs
import re
import zipfile

from django import forms
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import generic

from .models import Report, Trader


def logout(request):
    auth_logout(request)
    return redirect("/")

def IndexView(request):
    return render(request,'Login/login.html')


class UploadFileForm(forms.Form):
    file = forms.FileField(label="Choose File",widget=forms.ClearableFileInput(attrs={'multiple':True}))

class Weeks(generic.ListView):
    template_name = 'Login/weeks.html'
    context_object_name = "weeks"
    def get_queryset(self):
        data=Report.objects.all()
        all_weeks=[]
        for i in data:
            all_weeks+=re.findall(r'^WEEK[0-9]+',getattr(i,'name'))
        all_weeks=list(set(all_weeks))
        all_weeks.sort()
        return all_weeks

def ReportView(request):
    # email=request.user.get_username()+"@axxela.in"
    email="manoj.korrapati@axxela.in"
    trader_acc=Trader.objects.get(email=email)
    account=getattr(trader_acc,"account")
    week=request.GET.get('week','WEEK25')
    file_name=week+"/"+account+"_Report2.html"
    user_report=Report.objects.get(name=file_name)
    html_content=getattr(user_report,'report_file')
    html_content=html_content[2:]
    html_content=codecs.getdecoder("unicode-escape")(html_content)[0]
    return HttpResponse(html_content)
    return HttpResponse("")

def AdminView(request):
    if request.method=='POST':
        form=UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            if 'reports' in request.POST:
                Report.objects.all().delete()
                upfile=request.FILES['file']
                with zipfile.ZipFile(upfile) as f:
                    names=[html for html in f.namelist() if html.endswith('html')]
                    print(names)
                    for file_name in names:
                        name='/'.join(file_name.split('/')[1:])
                        content=f.open(file_name).read()
                        report=Report(name=name,report_file=content)
                        report.save()
                return HttpResponse("Updated")
            elif 'traders' in request.POST:
                Trader.objects.all().delete()
                request.FILES['file'].save_to_database(
                    model=Trader,
                    mapdict=['account','email']
                )
                return HttpResponse("done")

    form=UploadFileForm()
    return render(request,'Login/upload.html',context={'form':form})
