import argparse, configparser, datetime, glob,pathlib
from dateutil import parser
import ACILib

def main(start_date,end_date,shift='apjc'):

        
    #Reading current config from file
    #Docker WORKDIR is /HTTSDashboard/Apps/
    config = configparser.ConfigParser()
    config.read('./flask_tac/tacconfig.ini')
    
    tech_strip_list =  config[shift]['tech_strips'].split(',')
    
    ###### Path in Container setup ######

    
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
        
        event_path = config[shift]['_'.join(['eventpath',tech_strip.upper()])]
    
        dispatch_event_by_year = {} #{'2020':[events],'2021':[events]}
    
        start_datetime = parser.parse(start_date)
        end_datetime = parser.parse(end_date)
        
        print("Parsing Dispatched Case of tech_strip {} logfile {} to EventPath {}".format(tech_strip,logfilelist,event_path))
        
        ###### Parsing request date event ######
        for logfile in logfilelist:
            
            with open(logfile) as f:
                allevents = f.read()
            f.close()
            allevents = allevents.split("\n")
        
            #print('ParseRabbitMQ processing Dispatched Case from {}'.format(logfile))
            DispatchedEventList = ACILib.FindDispatchEvent(allevents,shift=shift,debug=False)
     
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
    argparser.add_argument('-p', action='store', dest='shift',default='apjc',type=str,help='Shift: apjc or emea')
    
    argresult = argparser.parse_args()
    
    start_date = argresult.start_date
    end_date = argresult.end_date
    shift = argresult.shift
    
    print("Dispatched Case Parsing Period {} - {} Shift: {}".format(start_date,end_date,shift))
        
    main(start_date,end_date,shift)
