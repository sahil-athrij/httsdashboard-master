import argparse, datetime, glob
from dateutil import parser
import ACILib

def GetSortedEventsFromDate(date='2020-04-05',allevents=[],InterestQueueName=[]):
    
    shift_hour,gmt_hour = ACILib.GetShiftHour(date)
    shift_start_hour,shift_end_hour = shift_hour[0],shift_hour[1]
        
    allevents_in_date = ACILib.GetRawEventsFromDate(allevents,date=date,shift_start_hour=shift_hour[0],shift_end_hour=shift_hour[1],debug=False)
    AcceptEventInOrderList = ACILib.CaseAcceptInOrderByTime(allevents_in_date,date=date,debug=False)
    
    InQueueEventList = ACILib.FindInQueueEvent(allevents_in_date,InterestQueueName,shift_start_hour=shift_hour[0],shift_end_hour=shift_hour[1],debug=False)
    InQueueEventInOrderList = ACILib.SortInQueueEventByTime(InQueueEventList,date=date,debug=False)
    
    return InQueueEventInOrderList,AcceptEventInOrderList

def main(start_date,end_date):
    
    InterestQueueName = ACILib.ACI_InterestQueueName
    ###### Path in Container setup ######
    flask_container_path = ''
    current_container_path = flask_container_path
    logfilename = current_container_path + '/HTTSDashboard/logs/RabbitMQ_ACI_Event.log*'
    logfilelist = glob.glob(logfilename)
    
    event_path = '/HTTSDashboard/logs/ACI/events/'
    acceptfilename = current_container_path + event_path + '*_AcceptEvent.txt'
    acceptfilelist = glob.glob(acceptfilename)
    inqueuefilename = current_container_path + event_path + '*_InQueueEvent.txt'
    inqueuefilelist = glob.glob(inqueuefilename)

    inqueue_event_by_year = {} #{'2020':[events],'2021':[events]}
    accept_event_by_year = {} #{'2020':[events],'2021':[events]}
    
    start_datetime = parser.parse(start_date)
    end_datetime = parser.parse(end_date)
    
    ###### Remving Events from Accept/InQueue file between start_date and end_date ######
    AcceptEventsFromFile = ACILib.FindAcceptEventsFromEventFile(acceptfilelist)
    InQueueEventsFromFile = ACILib.FindInQueueEventsFromEventFile(inqueuefilelist)
    
    cur_datetime = start_datetime
    while cur_datetime.date() <= end_datetime.date():
        #print('Removing events on {} from AcceptEvents'.format(cur_datetime.strftime("%Y-%m-%d")))
        AcceptEventsFromFile = ACILib.RemoveAcceptEventByDateFromFile(cur_datetime.strftime("%Y-%m-%d"),AcceptEventsFromFile)
        InQueueEventsFromFile = ACILib.RemoveInQueueEventByDateFromFile(cur_datetime.strftime("%Y-%m-%d"),InQueueEventsFromFile)
        cur_datetime = cur_datetime + datetime.timedelta(days=1)
    AcceptEvents_By_Year = AcceptEventsFromFile
    InQueueEvents_By_Year = InQueueEventsFromFile
    
    ###### Reading the RabbitMQ log files to get Accept/InQueue event for that day ######
    for logfile in logfilelist:
        with open(logfile) as f:
            allevents = f.read()
        f.close()
        allevents = allevents.split("\n")
        cur_datetime = start_datetime
        while cur_datetime.date() <= end_datetime.date():
            #print('ParseRabbitMQ processing AcceptEvent and InQueueEvent {} {}'.format(logfile,cur_datetime.strftime("%Y-%m-%d")))
            cur_date = cur_datetime.strftime("%Y-%m-%d")
            InQueueEventInOrderList,AcceptEventInOrderList = GetSortedEventsFromDate(date=cur_date,allevents=allevents,InterestQueueName=InterestQueueName)
            if len(AcceptEventInOrderList):
                #print("Adding {} Events for date {}".format(len(AcceptEventInOrderList),cur_date))
                AcceptEvents_By_Year = ACILib.AddAcceptEventByDateFromFile(cur_date, AcceptEventInOrderList, AcceptEvents_By_Year)
                InQueueEvents_By_Year = ACILib.AddInQueueEventByDateFromFile(cur_date,InQueueEventInOrderList,InQueueEvents_By_Year)
            cur_datetime = cur_datetime + datetime.timedelta(days=1)
    
    ###### This is the older way that Parsing RabbitMQ log by date and interate all the log files repeatly for different date. ######
    ###### Parsing request date event ######
    #for logfile in logfilelist:
    #    
    #    with open(logfile) as f:
    #        allevents = f.read()
    #    f.close()
    #    allevents = allevents.split("\n")
    #    cur_datetime = start_datetime
    #    
    #    while cur_datetime <= end_datetime:
    #        print('ParseRabbitMQ processing {} {}'.format(logfile,cur_datetime.strftime("%Y-%m-%d")))
    #        cur_date = cur_datetime.strftime("%Y-%m-%d")
    #        InQueueEventInOrderList,AcceptEventInOrderList = GetSortedEventsFromDate(date=cur_date,allevents=allevents,InterestQueueName=InterestQueueName)
    #        
    #        for event in InQueueEventInOrderList:
    #            caseno, casesev, queue, casetime = event.split('-~')
    #            eventyear = parser.parse(casetime).year
    #            if eventyear not in inqueue_event_by_year.keys():
    #                inqueue_event_by_year[eventyear] = []
    #            #print("{} {}".format(eventyear,event))
    #            inqueue_event_by_year[eventyear].append(event)
    #            
    #        for event in AcceptEventInOrderList:
    #            caseno, casesev, ccoid, workgroup, casetime = event.split('-~')
    #            eventyear = parser.parse(casetime).year
    #            if eventyear not in accept_event_by_year.keys():
    #                accept_event_by_year[eventyear] = []
    #            #print("{} {}".format(eventyear,event))
    #            accept_event_by_year[eventyear].append(event)
    #            
    #        cur_datetime = cur_datetime + datetime.timedelta(days=1)
              
    ##### Add/Delete events based on start_date , end_date ######
    #while len(inqueue_event_by_year) > 0:
    #    for year in inqueue_event_by_year:
    #        for event in inqueue_event_by_year[year][::-1]:
    #            print(event)
    #    break
        
    ###### Write to file ######
    for year,events in AcceptEvents_By_Year.items():
        with open(event_path+str(year)+'_AcceptEvent.txt', 'w+') as file:
            for event in events:
                file.write(event.strip()+'\n')
                
    for year,events in InQueueEvents_By_Year.items():
        with open(event_path+str(year)+'_InQueueEvent.txt', 'w+') as file:
            for event in events:
                file.write(event+'\n')
                
if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-s', action='store', dest='start_date',default=datetime.datetime.today().strftime("%Y-%m-%d"),help='Start date to parse')
    argparser.add_argument('-e', action='store', dest='end_date',default=datetime.datetime.today().strftime("%Y-%m-%d"),type=str,help='End date to parse')
    #argparser.add_argument('--force_overwrite', action='store_true', help="Force to overwrite all the events")
    
    argresult = argparser.parse_args()
    
    start_date = argresult.start_date
    end_date = argresult.end_date
    #force_overwrite = argresult.force_overwrite
    
    print("ParseRabbitMQ InQueue/Accept Events Period {} - {}".format(start_date,end_date))
        
    main(start_date,end_date)
