import codecs
import re
import zipfile
import datetime
from django import forms
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import generic
from .models import Report, Trader

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.core.mail import send_mail

def logout(request):
    auth_logout(request)
    return redirect("/")

def IndexView(request):
    return render(request,'Login/login.html')

def checkadmin(name):
    isadmin = False
    if name == "abhit.pahwa":
        isadmin = True
    return isadmin

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Choose File",widget=forms.ClearableFileInput(attrs={'multiple':True}))

def HomeView(request):
    isadmin=checkadmin(request.user.get_username())
    return render(request,'Login/home.html',context={'name':request.user.get_full_name(),'admin':isadmin})

class Weeks(generic.ListView):
    template_name = 'Login/weeks.html'
    context_object_name = "weeks"
    def get_context_data(self, *, object_list=None, **kwargs):
        context=super().get_context_data(**kwargs)
        context['name']=self.request.user.get_full_name().upper()
        context['admin']=checkadmin(self.request.user.get_username())
        return context
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

def GetWorksheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open('Limits').sheet1
    return sheet

def GetContext(request):
    isadmin = checkadmin(request.user.get_username())
    # email=request.user.get_username()+"@axxela.in"
    # trader_acc = Trader.objects.get(email=email)
    # account = getattr(trader_acc, "account")
    sheet = GetWorksheet()
    list_of_hashes = sheet.get_all_records()

    account = "LGBEE007"

    user_hashes = []
    trading_accounts = list(set(sheet.col_values(1)[1:]))

    stellar_options = []
    tt_options = []

    for dictionary in list_of_hashes:
        temp = {}
        options_temp = []
        for k, v in dictionary.items():
            if k == "Type":
                options_temp.append(v)
                temp[k] = v
            elif k == "Products":
                options_temp.append(v)
                temp[k] = v
            elif k == account:
                temp[k] = v
        if "Stellar" in dictionary.values():
            stellar_options.append(options_temp)
        elif "TT" in dictionary.values():
            tt_options.append(options_temp)
        user_hashes.append(temp)

    user_hashes = [dictionary for dictionary in user_hashes if dictionary[account] != ""]
    ct = [list(i.values()) for i in user_hashes]

    context_pass = {}
    context_pass["ct"] = ct
    context_pass["admin"] = isadmin
    context_pass["trading_accounts"] = trading_accounts
    context_pass['stellar'] = stellar_options
    context_pass['tt'] = tt_options

    return context_pass


def MyLimits(request):
    # email=request.user.get_username()+"@axxela.in"
    # trader_acc = Trader.objects.get(email=email)
    # account = getattr(trader_acc, "account")
    account = "LGBEE007"

    context_pass=GetContext(request)

    if request.method=="GET":
        return render(request,'Login/limits.html',context=context_pass)
    if request.method=="POST":
        if 'submit1' in request.POST.keys():
            subject="Request: Update Limits and Clips"
            inputs=[(name,request.POST[name])for name in request.POST.keys() if (name.startswith("limit") \
                                                                                 or name.startswith("clip")) \
                                                                                 and request.POST[name]!='']
            msg=""
            for inp in inputs:
                temp=inp[0].split()
                if temp[0]=="limit":
                    msg+="Product: "+temp[1]+"\nType: "+temp[2]+"\nRequested limit: "+inp[1]+"\n\n"
                elif temp[0]=="clip":
                    msg += "Product: " + temp[1] + "\nType: " + temp[2] + "\nRequested clip: " + inp[1] + "\n\n"


            if msg=="":
                context_pass["error"]=True
                return render(request,'Login/limits.html',context=context_pass)

            body="Hi, can you please process the following limits and clips update requests!\n\n" + \
                "Account: "+account+"\n\n" + msg +\
                "Thanks and Regards"+"\n" + \
                request.user.get_full_name()+"\n\n"+ \
                 "TimeStamp: " + str(datetime.datetime.now().strftime("%Y-%m-%d, %H:%M")) + "\n"

            context_pass["request_sent"]=True

            # send_mail(subject,body,"risk@axxela.in",["abhit.pahwa@axxela.in"],fail_silently=False)
            return render(request,'Login/limits.html',context=context_pass)
        elif 'submit2' in request.POST.keys():
            trading_acc = request.POST['acc']
            product = request.POST['prd']
            product_type = request.POST['prd-type']
            limit = request.POST['addlimit']
            clip = request.POST['addclip']

            subject = "Request: Add product"

            if limit == "" and clip == "":
                context_pass["error"] = True
                return render(request, 'Login/limits.html', context=context_pass)

            body = "Hi, can you please process the following request to add product!\n\n" + \
                   "Account: " + account + "\n" + \
                   "Product: " + product + "\n" + \
                   "Type: " + product_type + "\n" + \
                   "Limit: " + limit + "\n" + \
                   "Clip: " + clip + "\n\n" + \
                   "Thanks and Regards" + "\n" + \
                   request.user.get_full_name() + "\n\n" + \
                   "TimeStamp: " + str(datetime.datetime.now().strftime("%Y-%m-%d, %H:%M")) + "\n"
            context_pass["request_sent"] = True
            # send_mail(subject,body,"risk@axxela.in",["abhit.pahwa@axxela.in"],fail_silently=False)
            return render(request, 'Login/limits.html', context=context_pass)


