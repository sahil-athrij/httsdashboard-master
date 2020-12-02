import dateutil
from dateutil import parser
import datetime
import re
import os
import argparse 
import ACILib

#It was exected in the jupyter notebook container , path is different from flask container.

def main(date = datetime.datetime.today().strftime("%Y-%m-%d")):
    
    current_hour = datetime.datetime.now().hour    
    shift_hour,gmt_hour = ACILib.GetShiftHour(date)
    
    flask_container_path = ''
    current_container_path = flask_container_path
    sourcefile = current_container_path + '/HTTSDashboard/logs/RabbitMQ_SV_Event.log'
    sourcefiletime = os.path.getmtime(sourcefile)
    #print("{} {} {}".format(date,sourcefiletime,shift_hour))
    sourcefiledatetime = datetime.datetime.fromtimestamp(sourcefiletime) + datetime.timedelta(hours=(gmt_hour+shift_hour[0]))
    sourcefileformattime = sourcefiledatetime.strftime("%Y-%m-%d %H:%M:%S")
    
if __name__ == "__main__":
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-s', action='store', dest='start_date',default=datetime.datetime.today().strftime("%Y-%m-%d"),help='Start date to parse')
    argparser.add_argument('-e', action='store', dest='end_date',default=datetime.datetime.today().strftime("%Y-%m-%d"),type=str,help='End date to parse')
    argresult = argparser.parse_args()
    
    cur_datetime = parser.parse(argresult.start_date)
    end_datetime = parser.parse(argresult.end_date)
    
    while cur_datetime <= end_datetime:
        cur_date = cur_datetime.strftime("%Y-%m-%d")
        shift_hour,gmt_hour = ACILib.GetShiftHour(cur_date)
        print('Processing {} StartGMT {} GMT {}'.format(cur_date,shift_hour[0],gmt_hour,))
        main(cur_date)
        cur_datetime = cur_datetime + datetime.timedelta(days=1)