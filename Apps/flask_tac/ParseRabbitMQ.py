import argparse, configparser, datetime, glob, pathlib
from dateutil import parser
import ACILib

def GetSortedEventsFromDate(date='2020-04-05',allevents=[],shift='apjc',InterestQueueName=[]):
    
    shift_hour,_ = ACILib.GetShiftHour(date,shift=shift)
        
    allevents_in_date = ACILib.GetRawEventsFromDate(allevents,date=date,shift_start_hour=shift_hour[0],shift_end_hour=shift_hour[1],debug=False)
    AcceptEventInOrderList = ACILib.CaseAcceptInOrderByTime(allevents_in_date,date=date,debug=False)
    
    InQueueEventList = ACILib.FindInQueueEvent(allevents_in_date,InterestQueueName,shift_start_hour=shift_hour[0],shift_end_hour=shift_hour[1],debug=False)
    InQueueEventInOrderList = ACILib.SortInQueueEventByTime(InQueueEventList,date=date,debug=False)
    
    return InQueueEventInOrderList,AcceptEventInOrderList

def main(start_date,end_date,shift='apjc'):
    
    #Reading current config from file
    #Docker WORKDIR is /HTTSDashboard/Apps/
    config = configparser.ConfigParser()
    config.read('./flask_tac/tacconfig.ini')

    tech_strip_list =  config[shift]['tech_strips'].split(',')
    tech_strip_list = [strip for strip in tech_strip_list if strip]
    print("Parsing Shift {} TechStrip {} {} ".format(shift,len(tech_strip_list)," ".join(tech_strip_list)))
    
    for tech_strip in tech_strip_list:
        
        event_path = config[shift]['_'.join(['eventpath',tech_strip.upper()])]
        pathlib.Path(event_path).mkdir(parents=True, mode=775,exist_ok=True)
        logfilename = config[shift]['_'.join(['logfilename',tech_strip.upper()])]
        InterestQueueName = config[shift]['_'.join(['queuename',tech_strip.upper()])]
        InterestQueueName = InterestQueueName.split(',')
        
        ###### Path in Container setup ######
        flask_container_path = ''
        current_container_path = flask_container_path
        logfilename = current_container_path + logfilename
        logfilelist = glob.glob(logfilename)

        acceptfilename = current_container_path + event_path + '*_AcceptEvent.txt'
        acceptfilelist = glob.glob(acceptfilename)
        inqueuefilename = current_container_path + event_path + '*_InQueueEvent.txt'
        inqueuefilelist = glob.glob(inqueuefilename)

        #inqueue_event_by_year = {} #{'2020':[events],'2021':[events]}
        #accept_event_by_year = {} #{'2020':[events],'2021':[events]}

        start_datetime = parser.parse(start_date)
        end_datetime = parser.parse(end_date)
        
        #print("EventPath:{}\nlogfilename:{}\nInterestQueueName:{}\nAcceptfile:{}\nInQueuefile:{}".format(event_path,logfilename,InterestQueueName,acceptfilename,inqueuefilename))
    
        ###### Remving Events from Accept/InQueue file between start_date and end_date ######
        AcceptEventsFromFile = ACILib.FindAcceptEventsFromEventFile(acceptfilelist)
        _,InQueueEventsFromFile = ACILib.FindInQueueEventsFromEventFile(inqueuefilelist) 

        #print("AcceptEventsFromFile {}".format(AcceptEventsFromFile))
        #print("InQueueEventsFromFile {}".format(InQueueEventsFromFile))
        cur_datetime = start_datetime
        while cur_datetime.date() <= end_datetime.date():
            #print('Removing events on {} from AcceptEvents'.format(cur_datetime.strftime("%Y-%m-%d")))
            AcceptEventsFromFile = ACILib.RemoveAcceptEventByDateFromFile(cur_datetime.strftime("%Y-%m-%d"),AcceptEventsFromFile)
            InQueueEventsFromFile = ACILib.RemoveInQueueEventByDateFromFile(cur_datetime.strftime("%Y-%m-%d"),InQueueEventsFromFile)
            cur_datetime = cur_datetime + datetime.timedelta(days=1)
        AcceptEvents_By_Year = AcceptEventsFromFile
        InQueueEvents_By_Year = InQueueEventsFromFile
        #print("InQueueEvents_By_Year After RemoveInQueueEventByDateFromFile\n {}".format(InQueueEvents_By_Year))

        ###### Reading the RabbitMQ log files to get Accept/InQueue event for that day ######
        for logfile in logfilelist:

            #print("ParseRabbitMQ InQueue/Accept Events {} - {}".format(start_date,end_date,InterestQueueName))
            #print("ParseRabbitMQ Logfile - {}".format(logfilename))
            #print("ParseRabbitMQ EventPath - {}".format(event_path))
            #print("ParseRabbitMQ InterestQueueName - {}".format(InterestQueueName))

            with open(logfile) as f:
                allevents = f.read()
            f.close()
            allevents = allevents.split("\n")
            cur_datetime = start_datetime
            while cur_datetime.date() <= end_datetime.date():
                print('ParseRabbitMQ processing AcceptEvent and InQueueEvent {} {}'.format(logfile,cur_datetime.strftime("%Y-%m-%d")))
                cur_date = cur_datetime.strftime("%Y-%m-%d")
                InQueueEventInOrderList,AcceptEventInOrderList = GetSortedEventsFromDate(date=cur_date,allevents=allevents,shift=shift,InterestQueueName=InterestQueueName)
                #print("InQueue After GetSortedEventsFromDate\n {}".format(InQueueEventInOrderList))
                #print("Accept After GetSortedEventsFromDate {}".format(AcceptEventInOrderList))
                if len(AcceptEventInOrderList):
                    #print("Adding AcceptEvent {} Events for date {}".format(len(AcceptEventInOrderList),cur_date))
                    AcceptEvents_By_Year = ACILib.AddAcceptEventByDateFromFile(cur_date, AcceptEventInOrderList, AcceptEvents_By_Year)
                if len(InQueueEventInOrderList):
                    #print("Adding InQueueEvent {} Events for date {}".format(len(InQueueEventInOrderList),cur_date))
                    InQueueEvents_By_Year = ACILib.AddInQueueEventByDateFromFile(cur_date,InQueueEventInOrderList,InQueueEvents_By_Year)
                cur_datetime = cur_datetime + datetime.timedelta(days=1)
                #print("InQueueEvents_By_Year After AddInQueueEventByDateFromFile\n {}".format(InQueueEvents_By_Year))
                #print("AcceptEvents_By_Year After AddInQueueEventByDateFromFile\n {}".format(InQueueEvents_By_Year))
        #print("Accept by year {}".format(AcceptEvents_By_Year))

        ###### Write to file txt forma and json format######
        for year,events in AcceptEvents_By_Year.items():
            #AcceptEventsList = []
            with open(event_path+str(year)+'_AcceptEvent.txt', 'w+') as file:
                for event in events:
                    # caseno,casesev,ccoid,queue,timestamp = event.split('-~')
                    # AcceptEventsList.append([caseno,casesev,ccoid,queue,timestamp])
                    file.write(event.strip()+'\n')
            # with open(event_path+str(year)+'_AcceptEvent.json', 'w') as file:
            #     import json    
            #     json.dump({"2020":AcceptEventsList}, file)

        for year,events in InQueueEvents_By_Year.items():
            #InQueueEventsList = []
            with open(event_path+str(year)+'_InQueueEvent.txt', 'w+') as file:
                for event in events:
                    # caseno,casesev,queue,timestamp = event.split('-~')
                    # InQueueEventsList.append([caseno,casesev,queue,timestamp])
                    file.write(event+'\n')
            # with open(event_path+str(year)+'_InQueueEvent.json', 'w') as file:
            #     import json
            #     json.dump({"2020":InQueueEventsList}, file)

if __name__ == "__main__":
    
    '''
    The script is used to reading RabbitMQ log files and generating InQueue and Accept event for shift/tech_strip
    input/output file is defined in tacconfig.ini
    '''
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-s', action='store', dest='start_date',default=datetime.datetime.today().strftime("%Y-%m-%d"),help='Start date to parse')
    argparser.add_argument('-e', action='store', dest='end_date',default=datetime.datetime.today().strftime("%Y-%m-%d"),type=str,help='End date to parse')
    argparser.add_argument('-p', action='store', dest='shift',default='apjc',type=str,help='Shift: apjc or emea')
    #argparser.add_argument('--force_overwrite', action='store_true', help="Force to overwrite all the events")
    
    argresult = argparser.parse_args()
    
    start_date = argresult.start_date
    end_date = argresult.end_date
    shift = argresult.shift

    #force_overwrite = argresult.force_overwrite
    main(start_date,end_date,shift)