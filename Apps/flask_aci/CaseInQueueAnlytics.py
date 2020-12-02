import glob
import pandas as pd
from dateutil import parser
import datetime

def ReadInQueuefile(filename='/home/jovyan/HTTSDashboard/logs/ACI/CaseInQueue/*.txt'):
    
    CaseInQueueFileList = glob.glob(filename)

    for file in CaseInQueueFileList:
        
        #print(file)
        with open(file,'r') as f:
            InQueueEvents = f.readlines()
        f.close()
        print(InQueueEvents[0])
        ###### Add index ######
        InQueueEvents = [[idx,*line.strip().split('-~')] for idx,line in enumerate(InQueueEvents)]
        #print(InQueueEvents[10])
        
        ###### Split Date-Time to Date and Time columns ######
        InQueueEvents = [[*event,parser.parse(event[4]).strftime("%Y-%m-%d")] for event in InQueueEvents]
        InQueueEvents = [[*event,parser.parse(event[4]).strftime("%H:%M:%S")] for event in InQueueEvents]
        #print(InQueueEvents[10])
        
        ###### Add Weekdays start from 0(Monday) ######
        InQueueEvents = [[*event,parser.parse(event[4]).weekday()] for event in InQueueEvents]
        #print(InQueueEvents[10])
        
        pd_labels = ['Idx','No','Sev','Queue','DateTime','Date','Time','Weekday']
        df = pd.DataFrame.from_records(InQueueEvents,columns=pd_labels)
        
        return df
    
def main(start_date,end_date):
    
    df = ReadInQueuefile('/home/jovyan/HTTSDashboard/logs/ACI/CaseInQueue/*.txt')
    
    df = df[df['Date'].between('2020-02-27','2020-03-01', inclusive=True)]
    
    print(df)
    
if __name__ == "__main__":
    main('2020-02-27','2020-03-01')
