import datetime, re, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ACILib

today_date = datetime.datetime.today().strftime("%Y-%m-%d")
today_weekday = datetime.datetime.today().strftime("%A")

emailhost = "outbound.cisco.com"
FromEmail = "reportbot-aci@cisco.com"

#ToEmail = ['tonzeng@cisco.com']
ToEmail = ['eugenlau@cisco.com', 'rajbg@cisco.com']

#CCEmail = ['zdazhi@cisco.com','zdazhi@cisco.com']
#CCEmail = []
CCEmail = ['lindawa@cisco.com','jawalia@cisco.com']
###### For debugging, added myself ######
BCCEmail = ['zdazhi@cisco.com']

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = "{} ACI-APJC Tracking Report - {} ".format(today_date,today_weekday)
msg['From'] = FromEmail
msg['To'] = ", ".join(ToEmail)
msg['Cc'] = ", ".join(CCEmail)

dailyreportfilename = '/HTTSDashboard/logs/ACI/report/'+today_date+'.html'
with open(dailyreportfilename,'r') as file:
    dailyreportstringhtml = file.read()

###### TODO: List engineer and case volume in title ######
#Tot_Case_Reg = re.compile(r'Queue Case Volume -- Total (\d+)')
#OnShiftEngineer_Reg = re.compile('^Onshift Engineer (\d+)\+(\d+)')
#Tot_Case = 0
#Tot_Engr = 0
#for line in dailyreportstringhtml.split('\n'):
#  #print(line)
#  if re.search(Tot_Case_Reg,line):
#    Tot_Case = re.search(Tot_Case_Reg,line).group(1)
#    print(Tot_Case)
#  elif re.search(OnShiftEngineer_Reg,line):
#    Tot_Engr = int(re.search(OnShiftEngineer_Reg,line).group(1)) + \
#      int(re.search(OnShiftEngineer_Reg,line).group(2))
#    print(Tot_Engr)

# Create the body of the message (a plain-text and an HTML version).
bottom_html = '<br>This is system-generated email. Report is available at <a href="https://syd-htts-prd.cisco.com/ACI">ACI Tracking Report</a> Conact <a href="mailto:zdazhi@cisco.com">Derek</a> for any issue.'

html = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
       How are you?<br>
       Here is the <a href="http://www.python.org">link</a> you wanted.
    </p>
  </body>
</html>
"""

#part1 = MIMEText(head_html, 'text')
part2 = MIMEText(dailyreportstringhtml+bottom_html, 'html')

#msg.attach(part1)
msg.attach(part2)

mail = smtplib.SMTP(emailhost)
mail.ehlo()
mail.starttls()
#mail.login('userName', 'password')
mail.sendmail(FromEmail, ToEmail+CCEmail+BCCEmail, msg.as_string())
mail.quit()
