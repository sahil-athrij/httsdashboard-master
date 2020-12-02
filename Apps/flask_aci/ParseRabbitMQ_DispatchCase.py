import argparse, datetime, glob
from dateutil import parser
import ACILib

def main(start_date,end_date):
    
    InterestQueueName = ACILib.ACI_InterestQueueName
    ###### Path in Container setup ######
    flask_container_path = ''
    current_container_path = flask_container_path
    eventfilename = current_container_path + '/HTTSDashboard/logs/RabbitMQ_ACI_Event.log*'
    eventfilelist = glob.glob(eventfilename)

    event_path = '/HTTSDashboard/logs/ACI/events/'
    dispatch_event_by_year = {} #{'2020':[events],'2021':[events]}
    
    start_datetime = parser.parse(start_date)
    end_datetime = parser.parse(end_date)
    
    ###### Parsing request date event ######
    for eventfile in eventfilelist:
        
        with open(eventfile) as f:
            allevents = f.read()
        f.close()
        allevents = allevents.split("\n")
    
        print('ParseRabbitMQ processing Dispatched Case from {}'.format(eventfile))
        DispatchedEventList = ACILib.FindDispatchEvent(allevents,debug=False)
 
        for event in DispatchedEventList:
            caseno, casesev, casetime, casetitle = event.split('-~')
            eventyear = parser.parse(casetime).year
            if eventyear not in dispatch_event_by_year.keys():
                dispatch_event_by_year[eventyear] = []
            #print("{} {}".format(eventyear,event))
            dispatch_event_by_year[eventyear].append(event)
        
    ###### Write to file ######    
    for year,events in dispatch_event_by_year.items():
        with open(event_path+str(year)+'_DispatchedEvent.txt', 'w+') as file:
            print("Writting DispatchCase of year {}, there are {} dispatched cases".format(year,len(events)))
            for event in events:
                file.write(event+'\n')
                
if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-s', action='store', dest='start_date',default='2020-02-27',help='Start date to parse')
    argparser.add_argument('-e', action='store', dest='end_date',default=datetime.datetime.today().strftime("%Y-%m-%d"),type=str,help='End date to parse')
    #argparser.add_argument('--force_overwrite', action='store_true', help="Force to overwrite all the events")
    
    argresult = argparser.parse_args()
    
    start_date = argresult.start_date
    end_date = argresult.end_date
    #force_overwrite = argresult.force_overwrite
    
    print("Analytics Period {} - {}".format(start_date,end_date))
        
    main(start_date,end_date)
