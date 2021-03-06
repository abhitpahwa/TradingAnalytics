import codecs
import re
import zipfile
import datetime
from django import forms
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import generic
from .models import *
from .forms import *

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.core.mail import send_mail

def logout(request):
    auth_logout(request)
    # User.objects.get(username=request.user.get_username()).delete()
    return redirect("/")

def IndexView(request):
    return render(request,'Login/login.html')

def checkadmin(name):
    isadmin = False
    if name == "abhit.pahwa":
        isadmin = True
    return isadmin

def checkmentor(name):
    # print(name)
    ismentor=False
    mentors=set(Trader.objects.values_list("mentor"))
    mentors=[i[0] for i in mentors]
    if name+"@axxela.in" in mentors:
        ismentor=True
    return ismentor

def checkrisk(name):
    isrisk=True if name=="risk" else False
    return isrisk

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Choose File",widget=forms.ClearableFileInput(attrs={'multiple':True}))

def HomeView(request):
    isadmin=checkadmin(request.user.get_username())
    ismentor=checkmentor(request.user.get_username())
    isrisk=checkrisk(request.user.get_username())
    return render(request,'Login/home.html',context={'name':request.user.get_full_name(),'admin':isadmin,'mentor':ismentor,'risk':isrisk})

class Weeks(generic.ListView):
    template_name = 'Login/weeks.html'
    context_object_name = "weeks"
    def get_context_data(self, *, object_list=None, **kwargs):
        context=super().get_context_data(**kwargs)
        context['name']=self.request.user.get_full_name().upper()
        context['admin']=checkadmin(self.request.user.get_username())
        context['mentor']=checkmentor(self.request.user.get_username())
        context['risk']=checkrisk(self.request.user.get_username())
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
                    mapdict=['account','email','mentor']
                )
                return HttpResponse("done")
        else:
            if 'update expiry' in request.POST:
                sheet=GetWorksheet("expiry")
                list_of_hashes=sheet.get_all_records()
                for row in list_of_hashes:
                    for k in row.keys():
                        if k!="Exchange" and k!="Product":
                            if row[k]!='':
                                expiry_date=datetime.datetime.strptime(row[k],"%m/%d/%y %H:%M")
                                product=row["Exchange"]+" "+row["Product"]+" "+k
                                event_obj=Event(product=product,expiry=expiry_date)
                                event_obj.save()
    form=UploadFileForm()
    return render(request,'Login/upload.html',context={'form':form})

def GetWorksheet(required_sheet="limits"):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)
    if required_sheet=="limits":
        sheet = client.open('Limits').sheet1
    elif required_sheet=="expiry":
        sheet=client.open("Expiry").sheet1
    return sheet

def GetContext(request):
    isadmin = checkadmin(request.user.get_username())
    ismentor = checkmentor(request.user.get_username())
    isrisk = checkrisk(request.user.get_username())
    # email=request.user.get_username()+"@axxela.in"
    # trader_acc = Trader.objects.get(email=email)
    # account = getattr(trader_acc, "account")
    sheet = GetWorksheet()
    list_of_hashes = sheet.get_all_records()

    account = "LGBEE007"

    user_hashes = []
    trading_accounts = list(set(sheet.col_values(1)[1:]))
    trading_accounts.remove('TT')
    trading_accounts.insert(0,'TT')

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
            elif k=="Account":
                temp[k]=v
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
    context_pass["mentor"] = ismentor
    context_pass["risk"]= isrisk
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

            email = "manoj.korrapati@axxela.in"
            trader = Trader.objects.get(email=email)

            last_id = len(Request_Trader_Mapping.objects.all())

            request_ids=[]
            for inp in inputs:
                temp=inp[0].split()
                if temp[0]=="limit":
                    last_id += 1
                    new_id = "UpdateRequest-" + str(last_id)
                    curr_request=Request_Trader_Mapping(request_id=new_id, \
                                                        account=getattr(trader, 'account'), \
                                                        email=getattr(trader, 'email'))
                    curr_request.save()
                    request_ids.append(new_id)
                    msg+="Trading Software: "+temp[1]+"\nProduct: "+temp[2]+"\nType: "+temp[3]+"\nRequested limit: "+inp[1]+"\n\n"
                    curr_request_details=Request(request_id=Request_Trader_Mapping.objects.get(request_id=new_id),\
                                                 trading_software=temp[1],\
                                                 product=temp[2],product_type=temp[3],\
                                                 requested_limit=inp[1])
                    curr_request_details.save()
                elif temp[0]=="clip":
                    last_id += 1
                    new_id = "UpdateRequest-" + str(last_id)
                    curr_request = Request_Trader_Mapping(request_id=new_id,\
                                                          account=getattr(trader, 'account'),\
                                                          email=getattr(trader, 'email'))
                    curr_request.save()
                    request_ids.append(new_id)
                    msg +="Trading Software: "+temp[1]+"\nProduct: " + temp[2] + "\nType: " + temp[3] + "\nRequested clip: " + inp[1] + "\n\n"
                    curr_request_details = Request(request_id=Request_Trader_Mapping.objects.get(request_id=new_id), \
                                                   trading_software=temp[1], \
                                                   product=temp[2], product_type=temp[3], \
                                                   requested_clip=inp[1])
                    curr_request_details.save()

            if msg=="":
                context_pass["error"]=True
                return render(request,'Login/limits.html',context=context_pass)

            body="Hi, can you please process the following limits and clips update requests!\n\n" + \
                "Account: "+account+"\n\n" + msg +\
                "Thanks and Regards"+"\n" + \
                request.user.get_full_name()+"\n\n"+ \
                 "TimeStamp: " + str(datetime.datetime.now().strftime("%Y-%m-%d, %H:%M")) + "\n"


            context_pass["request_sent"]=True

            mentor=getattr(Trader.objects.get(email=email),'mentor')

            # send_mail(subject,body,"risk@axxela.in",[mentor],fail_silently=False)




            return render(request,'Login/limits.html',context=context_pass)
        elif 'submit2' in request.POST.keys():
            keys=request.POST.keys()
            trading_accs = [request.POST[i] for i in keys if "acc" in i]
            products=[request.POST[i] for i in keys if "prd" in i and "prd-type" not in i]
            product_types=[request.POST[i] for i in keys if "prd-type" in i]
            limits=[request.POST[i] for i in keys if "addlimit" in i]
            clips=[request.POST[i] for i in keys if "addclip" in i]

            subject = "Request: Add products"
            limits_empty=[i for i in limits if i!='']
            clips_empty=[i for i in clips if i!='']
            if len(limits_empty)==0 and len(clips_empty)==0:
                context_pass["error"] = True
                return render(request, 'Login/limits.html', context=context_pass)

            body = "Hi, can you please process the following request to add products!\n\n"
            body+="Account: "+account+"\n"

            email = "manoj.korrapati@axxela.in"
            trader = Trader.objects.get(email=email)

            last_id = len(Request_Trader_Mapping.objects.all())

            for i in range(len(trading_accs)):
                last_id += 1
                new_id = "AddRequest-" + str(last_id)
                curr_request = Request_Trader_Mapping(request_id=new_id, \
                                                      account=getattr(trader, 'account'), \
                                                      email=getattr(trader, 'email'))
                curr_request.save()
                prd="Trading Software: " + trading_accs[i] + "\n" + \
                    "Product: " + products[i] + "\n" + \
                    "Type: " + product_types[i] + "\n" + \
                    "Limit: " + limits[i] + "\n" + \
                   "Clip: " + clips[i] + "\n\n"
                body+=prd
                curr_limit=limits[i] if limits[i]!='' else 0
                curr_clip=clips[i] if clips[i]!='' else 0
                curr_request_details = Request(request_id=Request_Trader_Mapping.objects.get(request_id=new_id), \
                                               trading_software=trading_accs[i], \
                                               product=products[i], product_type=product_types[i], \
                                               requested_limit=curr_limit,requested_clip=curr_clip)
                curr_request_details.save()
            body+="Thanks and Regards" + "\n" + request.user.get_full_name() + "\n\n" + \
                   "TimeStamp: " + str(datetime.datetime.now().strftime("%Y-%m-%d, %H:%M")) + "\n"
            context_pass["request_sent"] = True

            mentor = getattr(Trader.objects.get(email=email), 'mentor')
            # # send_mail(subject,body,"risk@axxela.in",[mentor],fail_silently=False)
            return render(request, 'Login/limits.html', context=context_pass)

def RequestHistory(request):
    user_requests=Request_Trader_Mapping.objects.filter(email="manoj.korrapati@axxela.in")
    user_requests_details=[]
    for i in user_requests:
        req_id=i.request_id
        temp=[]
        temp.append(req_id)
        temp_obj=Request.objects.get(request_id=req_id)
        temp.append(getattr(temp_obj,'trading_software'))
        temp.append(getattr(temp_obj, 'product'))
        temp.append(getattr(temp_obj, 'product_type'))
        temp_limit=getattr(temp_obj, 'requested_limit')
        temp_clip=getattr(temp_obj, 'requested_clip')
        if temp_limit!=None:
            temp.append(temp_limit)
        else:
            temp.append('')
        if temp_clip!=None:
            temp.append(temp_clip)
        else:
            temp.append('')
        temp.append(getattr(i,'mentor_approval'))
        temp.append(getattr(i,'risk_approval'))
        user_requests_details.append(temp)
    user_requests_details.reverse()
    isadmin = checkadmin(request.user.get_username())
    ismentor = checkmentor(request.user.get_username())
    isrisk=checkrisk(request.user.get_username())
    return render(request,'Login/request_history.html',context={"admin":isadmin,"mentor":ismentor,\
                                                                "risk":isrisk,"requests":user_requests_details})

def MentorView(request):
    if request.method=="POST":
        approve_request_id=[i for i in request.POST.keys() if "approve" in i]
        reject_request_id=[i for i in request.POST.keys() if "reject" in i]
        if approve_request_id:
            approve_request_id=approve_request_id[0][7:]
            request_object = Request_Trader_Mapping.objects.get(request_id=approve_request_id)
            request_object.mentor_approval = "Approved"
        if reject_request_id:
            reject_request_id=reject_request_id[0][6:]
            request_object = Request_Trader_Mapping.objects.get(request_id=reject_request_id)
            request_object.mentor_approval = "Rejected"
        request_object.save()
    all_requests=Request_Trader_Mapping.objects.all()
    accounts=set([getattr(i,"email") for i in all_requests])
    traders=[Trader.objects.get(email=i) for i in list(accounts)]
    mentors=[getattr(i,"mentor") for i in traders]
    my_traders=[traders[i] for i in range(len(mentors)) if mentors[i]==request.user.email]
    my_traders_requests={}
    my_traders_detailed_requests={}
    for trader in my_traders:
        trader_email=getattr(trader, "email")
        trader_requests=Request_Trader_Mapping.objects.filter(email=trader_email,mentor_approval="Pending")
        temp=[[getattr(i,"request_id"),getattr(i,"mentor_approval"),getattr(i,"risk_approval")] for i in trader_requests]
        temp.reverse()
        temp_requests=[Request.objects.get(request_id=i) for i in [j[0] for j in temp]]
        temp_detail=[[getattr(i,"request_id"),getattr(i,"trading_software"),getattr(i,"product"),\
                      getattr(i,"product_type"),getattr(i,"requested_limit"),getattr(i,"requested_clip")] \
                     for i in temp_requests]
        for i in temp_detail:
            i[0]=getattr(i[0],'request_id')
        my_traders_requests[trader_email]=temp
        my_traders_detailed_requests[trader_email]=temp_detail

    isadmin = checkadmin(request.user.get_username())
    ismentor = checkmentor(request.user.get_username())
    isrisk=checkrisk(request.user.get_username())
    return render(request,'Login/mentor_view.html',context={"admin":isadmin,"mentor":ismentor,\
                                                            "risk":isrisk,\
                                                            "requests":my_traders_requests,\
                                                            'details':my_traders_detailed_requests})

def RiskView(request):
    if request.method == "POST":
        approve_request_id = [i for i in request.POST.keys() if "approve" in i]
        reject_request_id = [i for i in request.POST.keys() if "reject" in i]
        if approve_request_id:
            approve_request_id = approve_request_id[0][7:]
            request_object = Request_Trader_Mapping.objects.get(request_id=approve_request_id)
            request_object.risk_approval = "Approved"

            sheet = GetWorksheet()
            list_of_hashes = sheet.get_all_records()
            request_detail=Request.objects.get(request_id=approve_request_id)

            # email=getattr(request_object,'email')
            # trader_acc=getattr(Trader.objects.get(email=email),'account')
            # print(trader_acc)
            account="LGBEE009"


            trading_software=getattr(request_detail,'trading_software')
            product=getattr(request_detail,'product')
            product_type=getattr(request_detail,'product_type')
            limit=getattr(request_detail,'requested_limit')
            clip=getattr(request_detail,'requested_clip')
            print(trading_software,product,product_type)
            # print(list_of_hashes[0].keys())
            if limit:
                account_col=list(list_of_hashes[0].keys()).index(account)+1
                for i,row in enumerate(list_of_hashes):
                    if row["Account"]==trading_software and row["Products"]==product and row["Type"]==product_type:
                        row_col=i+2
                        break
                sheet.update_cell(row_col,account_col,limit)
        if reject_request_id:
            reject_request_id = reject_request_id[0][6:]
            request_object = Request_Trader_Mapping.objects.get(request_id=reject_request_id)
            request_object.risk_approval = "Rejected"
        request_object.save()
    context={}
    context["admin"]=checkadmin(request.user.get_username())
    context["mentor"]=checkmentor(request.user.get_username())
    context["risk"]=checkrisk(request.user.get_username())

    approved_requests=Request_Trader_Mapping.objects.filter(mentor_approval="Approved",risk_approval="Pending")
    request_brief=[[getattr(i,'request_id'),getattr(i,'email'),getattr(i,'account')] for i in approved_requests]
    request_brief.reverse()
    request_ids = [Request.objects.get(request_id=i) for i in [j[0] for j in request_brief]]
    request_detail = [[getattr(i, "request_id"), getattr(i, "trading_software"), getattr(i, "product"), \
                       getattr(i, "product_type"), getattr(i, "requested_limit"), getattr(i, "requested_clip")] \
                       for i in request_ids]
    for i in request_detail:
        i[0] = getattr(i[0], 'request_id')

    context['brief']=request_brief
    context['detail']=request_detail


    return render(request,'Login/risk_view.html',context=context)

def Support(request):
    context={}
    context["admin"]=checkadmin(request.user.get_username())
    context["mentor"]=checkmentor(request.user.get_username())
    context["risk"]=checkrisk(request.user.get_username())
    if context["risk"]:
        tickets=SupportDb.objects.all()
        tickets_dict={}
        for i in tickets:
            tickets_dict[i.ticket_id]=[i.subject,i.body,i.screenshot.url]
        context["tickets_dict"]=tickets_dict
        return render(request,'Login/support.html',context=context)
    form=SupportForm()
    context["form"]=form
    if request.method=="POST":
        print(request.POST.keys())
        last_id=len(SupportDb.objects.all())
        new_id="Ticket-"+str(last_id+1)
        subject=request.POST["subject"]
        body=request.POST["body"]
        screenshot=request.FILES["screenshot"]
        new_support=SupportDb(email=request.user.email,ticket_id=new_id,subject=subject,body=body,screenshot=screenshot)
        new_support.save()
    return render(request,'Login/support.html',context=context)

import datetime as dt

from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from django.utils.safestring import mark_safe

from .models import *
from .utils import Calendar
import calendar

class CalendarView(generic.ListView):
    model = Event
    template_name = 'Login/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # use today's date for the calendar
        # print(self.request.GET.get('month', None))
        d = get_date(self.request.GET.get('month', None))
        # print(d)
        # Instantiate our calendar class with today's year and date
        cal = Calendar(d.year, d.month)

        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(withyear=True)
        context['calendar'] = mark_safe(html_cal)
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)
        return context

def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return dt.date(year, month, day=1)
    return dt.datetime.today()

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - dt.timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + dt.timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month