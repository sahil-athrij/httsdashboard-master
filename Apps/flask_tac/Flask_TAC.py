from flask import Flask, request, jsonify
import configparser, datetime, os, re, ssl
from dateutil import parser

#app = Flask(__name__,static_url_path='/analytics_aci',static_folder = "/analytics_aci")
app = Flask(__name__)

def BuildDailyReport(shift='apjc',tech_strip='aci',select_date='2020-06-28',AlarmString=''):

    ###### Configuration Initialization #######
    config.read('./flask_tac/tacconfig.ini')

    general_frontend_html_dir = config[shift]['frontend_html']+'html/'
    general_commentfile = general_frontend_html_dir+'comment.txt'
    general_headerhtmlfile = general_frontend_html_dir+'header.html'
    general_bottomhtmlfile = general_frontend_html_dir+'bottom.html'

    tech_strip_frontend_html_dir = config[shift]['frontend_html']+tech_strip.upper()+'/html/'
    tech_strip_report_path = config[shift]['{}_{}'.format('reportpath',tech_strip)]
    tech_strip_commentfile = tech_strip_frontend_html_dir+'comment.txt'
    tech_strip_headerhtmlfile = tech_strip_frontend_html_dir+'header.html'
    tech_strip_bottomhtmlfile = tech_strip_frontend_html_dir+'bottom.html'
    tech_strip_dailyreportfilename = '{}{}_{}_{}.html'.format(tech_strip_report_path,select_date,shift.upper(),tech_strip.upper())

    comment = ""
    headerhtml = ""
    bottomhtml = ""
    dailyreportstringhtml = ""

    if os.path.exists(general_commentfile):
        with open(general_commentfile,'r') as file:
            comment = file.read()
    if os.path.exists(tech_strip_commentfile):
        with open(tech_strip_commentfile,'r') as file:
            comment = comment + file.read()
    commenthtml = comment.replace('\n','\n<br>')

    if os.path.exists(general_headerhtmlfile):
        with open(general_headerhtmlfile,'r') as file:
            headerhtml = file.read()
    if os.path.exists(tech_strip_headerhtmlfile):
        with open(tech_strip_headerhtmlfile,'r') as file:
            headerhtml = headerhtml+file.read()    

    if os.path.exists(tech_strip_bottomhtmlfile):
        with open(tech_strip_bottomhtmlfile,'r') as file:
            bottomhtml = file.read()
    if os.path.exists(general_bottomhtmlfile):
        with open(general_bottomhtmlfile,'r') as file:
            bottomhtml = bottomhtml + file.read()

    if os.path.exists(tech_strip_dailyreportfilename):
        with open(tech_strip_dailyreportfilename,'r') as file:
            dailyreportstringhtml = file.read()
    
    return headerhtml+AlarmString+dailyreportstringhtml+'<br>\n'+commenthtml+bottomhtml
    #return headerhtml+dailyreportstringhtml

def BuildAnalyticsReprt(shift='apjc',tech_strip='aci',analytics_start_date='2020-06-23',analytics_end_date='2020-06-28'):

    ###### Configuration Initialization #######
    config.read('./flask_tac/tacconfig.ini')
    frontend_html_dir = config[shift]['frontend_html']+tech_strip+'/html/'
    headerhtmlfile = frontend_html_dir+'header.html'
    bottomhtmlfile = frontend_html_dir+'bottom.html'

    analytics_start_datetime = parser.parse(analytics_start_date)
    analytics_end_datetime = parser.parse(analytics_end_date)

    if analytics_start_datetime < parser.parse('2020-02-27'):
        analytics_start_date = '2020-02-27'
    if analytics_end_datetime > datetime.datetime.today():
        analytics_end_date = datetime.datetime.today().strftime("%Y-%m-%d")
    
    import ACI_Analytics
    if analytics_end_date == datetime.datetime.today().strftime("%Y-%m-%d"):
        ACI_Analytics.main(analytics_start_date,analytics_end_date,force_overwrite=False)
    else:
        ACI_Analytics.main(analytics_start_date,analytics_end_date,force_overwrite=False)

    #analytics_dir = '/analytics_aci/{}_{}/'.format(analytics_start_date,analytics_end_date)
    analytics_dir = '/static/analytics_{}_{}/{}_{}/'.format(shift.upper(),tech_strip.upper(),analytics_start_date,analytics_end_date)

    headerhtml = ""
    bottomhtml = ""
    #analytics_html = analytics_dir+' '+inqueue_start_date+' '+inqueue_end_date+'<br>\n'
    
    analytics_html = "<H4>Refresh every 15 minutes, click refresh button of your brower to refresh it</H4><br>\n"
    analytics_html = analytics_html+"<table>\n  <tr>\n    <td>\n"
    analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Case_Per_Weekday.png')
    analytics_html = analytics_html+'    </td>\n    <td align="center">\n'
    analytics_html = analytics_html+'<a target="_blank" href="https://towardsdatascience.com/understanding-boxplots-5e2df7bcbd51" style="text-decoration:none; color:#0000FF;">What is boxplot?</a><br>'
#        analytics_html = analytics_html+"    </td>\n    <td>\n"
    analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Case_Taken_Per_Engr_Box.png') 

    analytics_html = analytics_html+"    </td>\n  </tr>\n</table>\n"
    
    analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Case_Taken_Per_Engr.png') 
    
    analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'OnShift_Engineer.png') 
    analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Total_Case_SYD_BLR.png')
    analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Total_Case_SYD_BLR_Ratio.png')
    analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Total_Case_All_Queues.png')
    
    analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Case_Per_Hour.png')
    analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Case_Per_3Hours.png')
    
    with open(headerhtmlfile,'r') as file:
        headerhtml = file.read()
    with open(bottomhtmlfile,'r') as file:
        bottomhtml = file.read()
    return headerhtml+analytics_html+'<br>\n'+bottomhtml

def RecordAccessLog(shift='apjc',tech_strip='aci'):

    with open("/HTTSDashboard/logs/TAC/.stats",'r') as file:
        stats = file.read()
    with open("/HTTSDashboard/logs/TAC/.stats",'w') as file:
        file.write(stats+"{} {} {} {} {}\n".format(shift.upper(),tech_strip.upper(),
        datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),request.environ['REMOTE_ADDR'],request.method))

@app.route("/")
def index():
    return "Hello, World!"

@app.route("/ACI",methods=['GET', 'POST'])
def index_aci():    
    
    RecordAccessLog(shift='apjc',tech_strip='aci')
    ###### General Variables ######
    shift = 'apjc'
    tech_strip = 'ACI'
    cur_datetime = datetime.datetime.today()
    form_type = ""
    ###### Report Variable Initialization ######
    AlarmString = ''
    select_datetime = datetime.datetime.today()
    #request_data = {} #for debug
    ###### Analytics Variable Initialization ######
    analytics_start_date = ""
    analytics_end_date = ""

    ###### Find out it is GET or POST, if it is POST, it is report POST or Analytics POST ######
    if request.method == 'GET':
        form_type = "report"

    elif request.method == 'POST' and 'report_date_form' in request.form.keys():
        #request_data = request.form.to_dict(flat=False)
        form_type = "report"
        report_date = request.form.get('report_date')
        if report_date:
            select_datetime = parser.parse(report_date)
        else:
            select_datetime = cur_datetime
        if cur_datetime < select_datetime:
            AlarmString = "Wrong Dat Selected - Showing Today<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = cur_datetime
        elif  select_datetime < parser.parse('2020-02-27'):
            AlarmString = "No eariler than 2020 Feb 27<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = parser.parse('2020-02-27')
    
    elif request.method == 'POST'and re.search(r'aci_analytics_\w+d_form'," ".join(request.form.keys())):
        #request_data = request.form.to_dict(flat=False)
        if 'aci_analytics_customized_form' in request.form.keys():
            form_type = "analytics"
            analytics_start_date = request.form.get('analytics_start_date')
            analytics_end_date = request.form.get('analytics_end_date')
            if not analytics_start_date:
                analytics_start_date = '2020-02-27'
            if not analytics_end_date:
                analytics_end_date = cur_datetime.strftime("%Y-%m-%d")
        elif re.search(r'aci_analytics_\w+d_form'," ".join(request.form.keys())):
            form_type = "analytics"
            period = re.search(r'aci_analytics_(\w+)d_form'," ".join(request.form.keys())).group(1)
            if period == 'all':
                analytics_start_date = '2020-02-27'
            else:
                analytics_start_date = (cur_datetime - datetime.timedelta(days=int(period)-1)).strftime("%Y-%m-%d")
            analytics_end_date = cur_datetime.strftime("%Y-%m-%d")

    if form_type == 'report':
        
        select_date = select_datetime.strftime("%Y-%m-%d")
        # request_data_html = ''
        # for key,value in request_data.items():
        #     request_data_html = request_data_html + 'Key {} Value {}<br>'.format(key,value)
        return BuildDailyReport(shift=shift,tech_strip=tech_strip,select_date=select_date,AlarmString=AlarmString)
    
    elif form_type == 'analytics':

        # request_data_html = ''
        # for key,value in request_data.items():
        #    request_data_html = request_data_html + 'Key {} Value {}<br>'.format(key,value)
        #return analytics_html+request_data_html
        #    
        return BuildAnalyticsReprt(shift,tech_strip,analytics_start_date,analytics_end_date)

@app.route("/COLLAB",methods=['GET', 'POST'])
def index_collab():    

    RecordAccessLog(shift='apjc',tech_strip='collab')
    ###### General Variables ######
    shift = 'apjc'
    tech_strip = 'COLLAB'
    cur_datetime = datetime.datetime.today()
    form_type = ""
    ###### Report Variable Initialization ######
    AlarmString = ''
    select_datetime = datetime.datetime.today()

    ###### Find out it is GET or POST, if it is POST, it is report POST or Analytics POST ######
    if request.method == 'GET':
        form_type = "report"
    elif request.method == 'POST' and 'report_date_form' in request.form.keys():
        #request_data = request.form.to_dict(flat=False)
        form_type = "report"
        report_date = request.form.get('report_date')
        if report_date:
            select_datetime = parser.parse(report_date)
        else:
            select_datetime = cur_datetime
        if cur_datetime < select_datetime:
            AlarmString = "Wrong Dat Selected - Showing Today<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = cur_datetime
        elif  select_datetime < parser.parse('2020-07-03'):
            AlarmString = "No eariler than 2020 Jul 3<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = parser.parse('2020-07-03')

    if form_type == 'report':
        select_date = select_datetime.strftime("%Y-%m-%d")
        return BuildDailyReport(shift=shift,tech_strip=tech_strip,select_date=select_date,AlarmString=AlarmString)

@app.route("/DCRS",methods=['GET', 'POST'])
def index_dcrs():    

    RecordAccessLog(shift='apjc',tech_strip='dcrs')
    ###### General Variables ######
    shift = 'apjc'
    tech_strip = 'DCRS'
    cur_datetime = datetime.datetime.today()
    form_type = ""
    ###### Report Variable Initialization ######
    AlarmString = ''
    select_datetime = datetime.datetime.today()

    ###### Find out it is GET or POST, if it is POST, it is report POST or Analytics POST ######
    if request.method == 'GET':
        form_type = "report"
    elif request.method == 'POST' and 'report_date_form' in request.form.keys():
        #request_data = request.form.to_dict(flat=False)
        form_type = "report"
        report_date = request.form.get('report_date')
        if report_date:
            select_datetime = parser.parse(report_date)
        else:
            select_datetime = cur_datetime
        if cur_datetime < select_datetime:
            AlarmString = "Wrong Dat Selected - Showing Today<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = cur_datetime
        elif  select_datetime < parser.parse('2020-06-12'):
            AlarmString = "No eariler than 2020 June 12<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = parser.parse('2020-06-12')

    if form_type == 'report':
        select_date = select_datetime.strftime("%Y-%m-%d")
        return BuildDailyReport(shift=shift,tech_strip=tech_strip,select_date=select_date,AlarmString=AlarmString)

@app.route("/ENT",methods=['GET', 'POST'])
def index_ent():    

    RecordAccessLog(shift='apjc',tech_strip='ent')
    ###### General Variables ######
    shift = 'apjc'
    tech_strip = 'ENT'
    cur_datetime = datetime.datetime.today()
    form_type = ""
    ###### Report Variable Initialization ######
    AlarmString = ''
    select_datetime = datetime.datetime.today()

    ###### Find out it is GET or POST, if it is POST, it is report POST or Analytics POST ######
    if request.method == 'GET':
        form_type = "report"
    elif request.method == 'POST' and 'report_date_form' in request.form.keys():
        #request_data = request.form.to_dict(flat=False)
        form_type = "report"
        report_date = request.form.get('report_date')
        if report_date:
            select_datetime = parser.parse(report_date)
        else:
            select_datetime = cur_datetime
        if cur_datetime < select_datetime:
            AlarmString = "Wrong Dat Selected - Showing Today<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = cur_datetime
        elif  select_datetime < parser.parse('2020-07-14'):
            AlarmString = "No eariler than 2020 July 14<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = parser.parse('2020-07-14')

    if form_type == 'report':
        select_date = select_datetime.strftime("%Y-%m-%d")
        return BuildDailyReport(shift=shift,tech_strip=tech_strip,select_date=select_date,AlarmString=AlarmString)

@app.route("/SEC",methods=['GET', 'POST'])
def index_sec():    

    RecordAccessLog(shift='apjc',tech_strip='sec')
    ###### General Variables ######
    shift = 'apjc'
    tech_strip = 'sec'
    cur_datetime = datetime.datetime.today()
    form_type = ""
    ###### Report Variable Initialization ######
    AlarmString = ''
    select_datetime = datetime.datetime.today()

    ###### Find out it is GET or POST, if it is POST, it is report POST or Analytics POST ######
    if request.method == 'GET':
        form_type = "report"
    elif request.method == 'POST' and 'report_date_form' in request.form.keys():
        #request_data = request.form.to_dict(flat=False)
        form_type = "report"
        report_date = request.form.get('report_date')
        if report_date:
            select_datetime = parser.parse(report_date)
        else:
            select_datetime = cur_datetime
        if cur_datetime < select_datetime:
            AlarmString = "Wrong Dat Selected - Showing Today<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = cur_datetime
        elif  select_datetime < parser.parse('2020-06-21'):
            AlarmString = "No eariler than 2020 June 21<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = parser.parse('2020-06-21')

    if form_type == 'report':
        select_date = select_datetime.strftime("%Y-%m-%d")
        return BuildDailyReport(shift=shift,tech_strip=tech_strip,select_date=select_date,AlarmString=AlarmString)

@app.route("/SP",methods=['GET', 'POST'])
def index_sp():    

    RecordAccessLog(shift='apjc',tech_strip='sp')
    ###### General Variables ######
    shift = 'apjc'
    tech_strip = 'sp'
    cur_datetime = datetime.datetime.today()
    form_type = ""
    ###### Report Variable Initialization ######
    AlarmString = ''
    select_datetime = datetime.datetime.today()

    ###### Find out it is GET or POST, if it is POST, it is report POST or Analytics POST ######
    if request.method == 'GET':
        form_type = "report"
    elif request.method == 'POST' and 'report_date_form' in request.form.keys():
        #request_data = request.form.to_dict(flat=False)
        form_type = "report"
        report_date = request.form.get('report_date')
        if report_date:
            select_datetime = parser.parse(report_date)
        else:
            select_datetime = cur_datetime
        if cur_datetime < select_datetime:
            AlarmString = "Wrong Dat Selected - Showing Today<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = cur_datetime
        elif  select_datetime < parser.parse('2020-06-21'):
            AlarmString = "No eariler than 2020 June 21<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = parser.parse('2020-06-21')

    if form_type == 'report':
        select_date = select_datetime.strftime("%Y-%m-%d")
        return BuildDailyReport(shift=shift,tech_strip=tech_strip,select_date=select_date,AlarmString=AlarmString)

@app.route("/SV",methods=['GET', 'POST'])
def index_sv():    

    RecordAccessLog(shift='apjc',tech_strip='sv')
    ###### General Variables ######
    shift = 'apjc'
    tech_strip = 'SV'
    cur_datetime = datetime.datetime.today()
    form_type = ""
    ###### Report Variable Initialization ######
    AlarmString = ''
    select_datetime = datetime.datetime.today()

    ###### Find out it is GET or POST, if it is POST, it is report POST or Analytics POST ######
    if request.method == 'GET':
        form_type = "report"
    elif request.method == 'POST' and 'report_date_form' in request.form.keys():
        #request_data = request.form.to_dict(flat=False)
        form_type = "report"
        report_date = request.form.get('report_date')
        if report_date:
            select_datetime = parser.parse(report_date)
        else:
            select_datetime = cur_datetime
        if cur_datetime < select_datetime:
            AlarmString = "Wrong Dat Selected - Showing Today<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = cur_datetime
        elif  select_datetime < parser.parse('2020-04-27'):
            AlarmString = "No eariler than 2020 April 27<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = parser.parse('2020-04-27')

    if form_type == 'report':
        select_date = select_datetime.strftime("%Y-%m-%d")
        return BuildDailyReport(shift=shift,tech_strip=tech_strip,select_date=select_date,AlarmString=AlarmString)

@app.route("/ACI_EU",methods=['GET', 'POST'])
def index_aci_eu():    

    RecordAccessLog(shift='emea',tech_strip='aci')
    ###### General Variables ######
    shift = 'emea'
    tech_strip = 'aci'
    cur_datetime = datetime.datetime.today()
    form_type = ""
    ###### Report Variable Initialization ######
    AlarmString = ''
    select_datetime = datetime.datetime.today()

    ###### Find out it is GET or POST, if it is POST, it is report POST or Analytics POST ######
    if request.method == 'GET':
        form_type = "report"
    elif request.method == 'POST' and 'report_date_form' in request.form.keys():
        #request_data = request.form.to_dict(flat=False)
        form_type = "report"
        report_date = request.form.get('report_date')
        if report_date:
            select_datetime = parser.parse(report_date)
        else:
            select_datetime = cur_datetime
        if cur_datetime < select_datetime:
            AlarmString = "Wrong Dat Selected - Showing Today<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = cur_datetime
        elif  select_datetime < parser.parse('2020-06-12'):
            AlarmString = "No eariler than 2020 June 12<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = parser.parse('2020-06-12')

    if form_type == 'report':
        select_date = select_datetime.strftime("%Y-%m-%d")
        return BuildDailyReport(shift=shift,tech_strip=tech_strip,select_date=select_date,AlarmString=AlarmString)

@app.route("/ACI_Legacy",methods=['GET', 'POST'])
def index_aci_legacy():    

    shift = 'apjc'
    tech_strip = 'aci'

    config.read('./flask_tac/tacconfig.ini')
    frontend_html_dir = config[shift]['frontend_html']+tech_strip+'/html/'
    report_path = config[shift]['{}_{}'.format('reportpath',tech_strip)]
    commentfile = frontend_html_dir+'comment.txt'
    headerhtmlfile = frontend_html_dir+'header.html'
    bottomhtmlfile = frontend_html_dir+'bottom.html'
    
    cur_datetime = datetime.datetime.today()
    select_datetime = datetime.datetime.today()
    
    analytics_start_date = ""
    analytics_end_date = ""
    analytics_start_datetime = cur_datetime
    analytics_end_datetime = cur_datetime
    
    AlarmString = ""
    form_type = ""
    
    if request.method == 'GET':
        form_type = "report"
        
    elif request.method == 'POST' and 'report_date_form' in request.form:
        form_type = "report"
        report_date = request.form.get('report_date')
        if report_date:
            select_datetime = parser.parse(report_date)
        else:
            select_datetime = cur_datetime
        
        if cur_datetime < select_datetime:
            AlarmString = "Wrong Dat Selected - Showing Today<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = cur_datetime
        elif  select_datetime < parser.parse('2020-02-27'):
            AlarmString = "No eariler than 2020 Feb 27<br>".format(select_datetime.strftime("%Y-%m-%d"))
            select_datetime = parser.parse('2020-02-27')
            
    elif request.method == 'POST':
        #return " ".join(request.form.keys())
        if 'aci_analytics_customized_form' in request.form:
            form_type = "analytics"
            analytics_start_date = request.form.get('analytics_start_date')
            analytics_end_date = request.form.get('analytics_end_date')
            if not analytics_start_date:
                analytics_start_date = '2020-02-27'
            if not analytics_end_date:
                analytics_end_date = cur_datetime.strftime("%Y-%m-%d")

        elif re.search(r'aci_analytics_\w+d_form'," ".join(request.form.keys())):
            form_type = "analytics"
            period = re.search(r'aci_analytics_(\w+)d_form'," ".join(request.form.keys())).group(1)
            if period == 'all':
                analytics_start_date = '2020-02-27'
            else:
                analytics_start_date = (cur_datetime - datetime.timedelta(days=int(period)-1)).strftime("%Y-%m-%d")
            analytics_end_date = cur_datetime.strftime("%Y-%m-%d")
        
    if form_type == 'report':
        ###### GET Method result ######
        commentfile = '/HTTSDashboard/logs/TAC/APJC/ACI/html/comment.txt'
        headerhtmlfile = '/HTTSDashboard/logs/TAC/APJC/ACI/html/header.html'
        bottomhtmlfile = '/HTTSDashboard/logs/TAC/APJC/ACI/html/bottom.html'
        dailyreportfilename = '{}{}_{}_{}.html'.format(report_path,select_datetime.strftime("%Y-%m-%d"),shift.upper(),tech_strip.upper())

        comment = ""
        headerhtml = ""
        bottomhtml = ""
        dailyreportstringhtml = ""

        with open(commentfile,'r') as file:
            comment = file.read()
        commenthtml = comment.replace('\n','\n<br>')
        with open(headerhtmlfile,'r') as file:
            headerhtml = file.read()
        with open(bottomhtmlfile,'r') as file:
            bottomhtml = file.read()
        with open(dailyreportfilename,'r') as file:
            dailyreportstringhtml = file.read()
        return headerhtml+AlarmString+dailyreportstringhtml+'<br>\n'+commenthtml+bottomhtml
    
    elif form_type == 'analytics':
        
        analytics_start_datetime = parser.parse(analytics_start_date)
        analytics_end_datetime = parser.parse(analytics_end_date)
        if analytics_start_datetime < parser.parse('2020-02-27'):
            analytics_start_date = '2020-02-27'
        if analytics_end_datetime > cur_datetime:
            analytics_end_date = cur_datetime.strftime("%Y-%m-%d")
        
        import ACI_Analytics
        if analytics_end_date == cur_datetime.strftime("%Y-%m-%d"):
            ACI_Analytics.main(analytics_start_date,analytics_end_date,force_overwrite=False)
        else:
            ACI_Analytics.main(analytics_start_date,analytics_end_date,force_overwrite=False)
            
        headerhtmlfile = '/HTTSDashboard/logs/TAC/APJC/ACI/html/header.html'
        bottomhtmlfile = '/HTTSDashboard/logs/TAC/APJC/ACI/html/bottom.html'
        analytics_dir = '/static/'+analytics_start_date+'_'+analytics_end_date+'/'
        headerhtml = ""
        bottomhtml = ""
        #analytics_html = analytics_dir+' '+inqueue_start_date+' '+inqueue_end_date+'<br>\n'
        
        analytics_html = "<H4>Refresh every 15 minutes, click refresh button of your brower to refresh it</H4><br>\n"
        analytics_html = analytics_html+"<table>\n  <tr>\n    <td>\n"
        analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Case_Per_Weekday.png')
        analytics_html = analytics_html+'    </td>\n    <td align="center">\n'
        analytics_html = analytics_html+'<a target="_blank" href="https://towardsdatascience.com/understanding-boxplots-5e2df7bcbd51" style="text-decoration:none; color:#0000FF;">What is boxplot?</a><br>'
#        analytics_html = analytics_html+"    </td>\n    <td>\n"
        analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Case_Taken_Per_Engr_Box.png') 

        analytics_html = analytics_html+"    </td>\n  </tr>\n</table>\n"
        
        analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Case_Taken_Per_Engr.png') 
        
        analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'OnShift_Engineer.png') 
        analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Total_Case_SYD_BLR.png')
        analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Total_Case_SYD_BLR_Ratio.png')
        analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Total_Case_All_Queues.png')
        
        analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Case_Per_Hour.png')
        analytics_html = analytics_html+"<img src=\"{}\"/><br>\n".format(analytics_dir+'Case_Per_3Hours.png')
        with open(headerhtmlfile,'r') as file:
             headerhtml = file.read()
        with open(bottomhtmlfile,'r') as file:
             bottomhtml = file.read()
        return headerhtml+analytics_html+'<br>\n'+bottomhtml
        
if __name__ == '__main__':
    
    #Reading current config from file
    config = configparser.ConfigParser()
    import os
    print(os.getcwd())
    config.read('Apps/flask_tac/config.ini')
    print(config.__dict__)
    ## TODO. Remove "pip install pyOpenSSL" and use an actual cert.
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_NONE
    context.load_verify_locations(config['ServerKey']['CA'])
    context.load_cert_chain(config['ServerKey']['ServerCert'],config['ServerKey']['SeverPriateKey'])
    app.run(host= '0.0.0.0', port=443, ssl_context=context, debug=True)
