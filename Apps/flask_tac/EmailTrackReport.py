import argparse, configparser, datetime, glob, os, re, smtplib
from dateutil import parser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ACILib

def sendemail(shift='apjc',tech_strip='aci',date=datetime.datetime.today().strftime("%Y-%m-%d"),config={}):
    
    if config[shift]['email_enabled_{}'.format(tech_strip.lower())] == 'no':
        print("Disable emaling to {} {}".format(shift,tech_strip))
        return
    else:
        #pass
        print("Sending email to {} {}".format(shift,tech_strip))
        
    messagefromfile = ''
    messagesofdates = []
    message_for_date = {}
    
    #today_date = datetime.datetime.today().strftime("%Y-%m-%d")
    #today_weekday = datetime.datetime.today().strftime("%A")
    date_weekday = parser.parse(date).strftime("%A")
    
    container_path = ''
    reportpath = container_path+config[shift]['_'.join(['reportpath',tech_strip.upper()])]
    htmlpath = '{}/html/'.format(container_path+config[shift]['frontend_html'],)
    
    messagefiles = glob.glob(htmlpath+'../../messages/*_message.txt')
    #print(messagefiles)
    for messagefile in messagefiles:
        messagefromfile = ''
        with open(messagefile) as f:
            messagefromfile = f.read()
        f.close()
    messagesofdates = messagesofdates + messagefromfile.split("\n")
    #print(messagesofdates)
    for message in messagesofdates:
        if not message:
            continue
        #<p style="color:blue">This is another paragraph.</p>
        message_for_date[message[:10]] = '<br><p style="color:red">{}</p><br>\n'.format(message[11:])
    if date in message_for_date.keys():
        print(message_for_date[date])
    else:
        message_for_date[date] = ''
    
    FromEmail = config[shift]['email_from_{}'.format(tech_strip.lower())]
    
    ToEmail = [ccoid+'@cisco.com' for ccoid in  config[shift]['workgroup_{}_mgr'.format(tech_strip.lower())].split(',')]
    #ToEmail = ['daszhang@cisco.com']
    CCEmail = [ccoid+'@cisco.com' for ccoid in  config[shift]['workgroup_{}_tl'.format(tech_strip.lower())].split(',')]
    #CCEmail = ['daszhang@cisco.com']
    BCCEmail = ['zdazhi@cisco.com', 'daszhang@cisco.com', 'jaehkim@cisco.com']
    emailhost = "outbound.cisco.com"

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "{} {}-{} Tracking Report - {} [SAMPLE v0.2]".format(date,shift.upper(),tech_strip.upper(),date_weekday)
    msg['From'] = FromEmail
    msg['To'] = ", ".join(ToEmail)
    msg['Cc'] = ", ".join(CCEmail)
    
    reportfile = "{}{}_{}_{}.html".format(reportpath,date,shift.upper(),tech_strip.upper())
    with open(reportfile,'r') as file:
        dailyreportstringhtml = file.read()
    
    bottom_html = '<br>This is system-generated email.<br>'
    if shift == 'emea' and tech_strip == 'aci':
        bottom_html = bottom_html + 'Live report is also available at <a href="https://syd-htts-prd.cisco.com/{}_EU">{}_EU Report</a>.  '.format(tech_strip.upper(),tech_strip.upper())
    else:
        bottom_html = bottom_html + 'Live report is also available at <a href="https://syd-htts-prd.cisco.com/{}">{} Report</a>.  '.format(tech_strip.upper(),tech_strip.upper())
    bottom_html = bottom_html + 'Contact <a href="mailto:daszhang@cisco.com">Shawn</a> <a href="mailto:jaehkim@cisco.com">Jae</a> for any issue.'

    #part1 = MIMEText(head_html, 'text')
    part2 = MIMEText(message_for_date[date]+dailyreportstringhtml+bottom_html, 'html')
    
    #print("From {} To {} CC {} BCC {}".format(FromEmail,ToEmail,CCEmail,BCCEmail))
    #print("Email Body {}".format(part2))
    
    #msg.attach(part1)
    msg.attach(part2)
    mail = smtplib.SMTP(emailhost)
    mail.ehlo()
    mail.starttls()
    #mail.login('userName', 'password')
    mail.sendmail(FromEmail, ToEmail+CCEmail+BCCEmail, msg.as_string())
    mail.quit()

if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', action='store', dest='date',default=datetime.datetime.today().strftime("%Y-%m-%d"),type=str,help='DateToSendFormat:2020-06-10')
    argparser.add_argument('-p', action='store', dest='shift',default='apjc',type=str,help='Shift:apjc|emea')
    argparser.add_argument('-t', action='store', dest='tech_strip',default='aci',type=str,help='TechStrip:aci')
    argresult = argparser.parse_args()

    shift = argresult.shift
    tech_strip = argresult.tech_strip
    datetosend = argresult.date
    
    #Reading current config from file
    #Docker WORKDIR is /HTTSDashboard/Apps/
    config = configparser.ConfigParser()
    config.read('./flask_tac/tacconfig.ini')
    
    tech_strip_list =  config[shift]['tech_strips'].split(',')
    tech_strip_list = [strip for strip in tech_strip_list if strip]
    
    for tech_strip in tech_strip_list:
        sendemail(shift=shift,tech_strip=tech_strip,date=datetime.datetime.today().strftime("%Y-%m-%d"),config=config)
