from flask import Flask, request, jsonify
import configparser, datetime, re, ssl
from dateutil import parser

#Reading current config from file
config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello, World!"

@app.route("/ACI",methods=['GET', 'POST'])
def index_aci():    
    
    with open("/HTTSDashboard/logs/TAC/.stats",'r') as file:
        stats = file.read()
    with open("/HTTSDashboard/logs/TAC/.stats",'w') as file:
        file.write(stats+"ACI {} {} {}\n".format(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),request.environ['REMOTE_ADDR'],request.method))
       
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
        commentfile = '/HTTSDashboard/logs/ACI/html/comment.txt'
        headerhtmlfile = '/HTTSDashboard/logs/ACI/html/header.html'
        bottomhtmlfile = '/HTTSDashboard/logs/ACI/html/bottom.html'
        dailyreportfilename = '/HTTSDashboard/logs/ACI/report/'+select_datetime.strftime("%Y-%m-%d")+'.html'

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
            
        headerhtmlfile = '/HTTSDashboard/logs/ACI/html/header.html'
        bottomhtmlfile = '/HTTSDashboard/logs/ACI/html/bottom.html'
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

@app.route("/ACI_NEW",methods=['GET'])
def index_aci_new():    

    with open("/HTTSDashboard/logs/TAC/.stats",'r') as file:
        stats = file.read()
    with open("/HTTSDashboard/logs/TAC/.stats",'w') as file:
        file.write(stats+"ACI_NEW {} {} {}\n".format(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),request.environ['REMOTE_ADDR'],request.method))
       
    dailyreportstringhtml = ''
    
    select_datetime = datetime.datetime.today()
    dailyreportfilename = '/HTTSDashboard/logs/TAC/APJC/ACI/report/'+select_datetime.strftime("%Y-%m-%d")+'_APJC_ACI.html'
    with open(dailyreportfilename,'r') as file:
        dailyreportstringhtml = file.read()
            
    return dailyreportstringhtml

@app.route("/SEC",methods=['GET'])
def index_sec():    

    with open("/HTTSDashboard/logs/TAC/.stats",'r') as file:
        stats = file.read()
    with open("/HTTSDashboard/logs/TAC/.stats",'w') as file:
        file.write(stats+"SEC {} {} {}\n".format(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),request.environ['REMOTE_ADDR'],request.method))
       
    dailyreportstringhtml = ''
    
    select_datetime = datetime.datetime.today()
    dailyreportfilename = '/HTTSDashboard/logs/TAC/APJC/SEC/report/'+select_datetime.strftime("%Y-%m-%d")+'_APJC_SEC.html'
    with open(dailyreportfilename,'r') as file:
        dailyreportstringhtml = file.read()
            
    return dailyreportstringhtml

@app.route("/SV",methods=['GET'])
def index_sv():    

    with open("/HTTSDashboard/logs/TAC/.stats",'r') as file:
        stats = file.read()
    with open("/HTTSDashboard/logs/TAC/.stats",'w') as file:
        file.write(stats+"SV {} {} {}\n".format(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),request.environ['REMOTE_ADDR'],request.method))
       
    dailyreportstringhtml = ''
    
    select_datetime = datetime.datetime.today()
    dailyreportfilename = '/HTTSDashboard/logs/TAC/APJC/SV/report/'+select_datetime.strftime("%Y-%m-%d")+'_APJC_SV.html'
    with open(dailyreportfilename,'r') as file:
        dailyreportstringhtml = file.read()
            
    return dailyreportstringhtml

@app.route("/DCRS",methods=['GET'])
def index_dcrs():    

    with open("/HTTSDashboard/logs/TAC/.stats",'r') as file:
        stats = file.read()
    with open("/HTTSDashboard/logs/TAC/.stats",'w') as file:
        file.write(stats+"DCRS {} {} {}\n".format(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),request.environ['REMOTE_ADDR'],request.method))
       
    dailyreportstringhtml = ''
    
    select_datetime = datetime.datetime.today()
    dailyreportfilename = '/HTTSDashboard/logs/TAC/APJC/DCRS/report/'+select_datetime.strftime("%Y-%m-%d")+'_APJC_DCRS.html'
    with open(dailyreportfilename,'r') as file:
        dailyreportstringhtml = file.read()
            
    return dailyreportstringhtml

@app.route("/ACI_EU",methods=['GET'])
def index_aci_eu():    

    with open("/HTTSDashboard/logs/TAC/.stats",'r') as file:
        stats = file.read()
    with open("/HTTSDashboard/logs/TAC/.stats",'w') as file:
        file.write(stats+"ACI_EU {} {} {}\n".format(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),request.environ['REMOTE_ADDR'],request.method))
       
    dailyreportstringhtml = ''
    
    select_datetime = datetime.datetime.today()
    dailyreportfilename = '/HTTSDashboard/logs/TAC/EMEA/ACI/report/'+select_datetime.strftime("%Y-%m-%d")+'_EMEA_ACI.html'
    with open(dailyreportfilename,'r') as file:
        dailyreportstringhtml = file.read()
            
    return dailyreportstringhtml

if __name__ == '__main__':
    ## TODO. Remove "pip install pyOpenSSL" and use an actual cert.
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_NONE
    context.load_verify_locations(config['ServerKey']['CA'])
    context.load_cert_chain(config['ServerKey']['ServerCert'],config['ServerKey']['SeverPriateKey'])
    app.run(host= '0.0.0.0', port=443, ssl_context=context, debug=True)
