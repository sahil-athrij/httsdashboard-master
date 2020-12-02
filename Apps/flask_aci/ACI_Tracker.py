import argparse, copy, datetime, glob,os
from dateutil import parser
import ACILib

def GenerateHTMLfile(date,sourcefileformattime,dispatchcasefiles,CaseQty,CaseStatsDic,OnShiftEngrList,CaseTakenDicInclNo,InQueueEventInOrderListWithEngr):
    
    dailyreportstring = "{} Queue Case Volume -- Total {} *** Update time AEST/AEDT: {}\n".format(date,sum(CaseQty.values()),sourcefileformattime)
    dailyreportstring = dailyreportstring+"==================\n"
    for case_type, case_volume in CaseQty.items():
        dailyreportstring = dailyreportstring+"{}:{}\n".format(case_type,case_volume)
    
    dailyreportstring = dailyreportstring+'\n'
    dailyreportstring = dailyreportstring+"{} Sydney Workgroup -- Taken Case:{}\n".format(date,CaseStatsDic['SydTakenVol'])
    dailyreportstring = dailyreportstring+"==================\n"
    dailyreportstring = dailyreportstring+"Onshift Engineer {}+{}\n".format(len(CaseTakenDicInclNo['SYD']),len(CaseTakenDicInclNo['SYD_Other']))
                                                                        
    #dailyreportstring = dailyreportstring+"SYD Queue Case {} FTS:{} P1:{} P2:{} P3:{} P4:{} UC:{}\n".format(CaseStatsDic['SydQueueVol'],*CaseStatsDic['SydQueueVolByPri'])
    dailyreportstring = dailyreportstring+"SYD Taken Case P1:{} P2:{} P3:{} P4:{} --- including  FTS:{} UC:{}\n".format(*CaseStatsDic['SydTakenVolByPri'][1:5],CaseStatsDic['SydTakenVolByPri'][0],CaseStatsDic['SydTakenVolByPri'][5])
    dailyreportstring = dailyreportstring+"SYD OnShift Engineer: {}\nSYD Other Engineer: {}\n".format(" ".join(CaseStatsDic['SydOnShiftEngr'])," ".join(CaseStatsDic['SYDHelper']))
    
    if len(CaseStatsDic['SydOnShiftEngr']) != 0 and False:
        dailyreportstring=dailyreportstring+"SYD Case/Engineer (TotCase/OnShift) {0:.2f}\n".format(CaseStatsDic['SydTakenVol']/len(CaseStatsDic['SydOnShiftEngr']))
        dailyreportstring=dailyreportstring+"SYD Case/Engineer (OnshiftEngrTakenCase/Onshift) {0:.2f}\n".format(CaseStatsDic['SydOnShiftEngrCaseVol']/len(CaseStatsDic['SydOnShiftEngr']))
        dailyreportstring=dailyreportstring+"SYD Case/Engineer (TotCase/(Onsfhit+Other)) {0:.2f}\n".format(CaseStatsDic['SydTakenVol']/(len(CaseStatsDic['SYDHelper'])+len(CaseStatsDic["SydOnShiftEngr"])))
    
    dailyreportstring = dailyreportstring+'\n'
    
    dailyreportstring = dailyreportstring+"{} Bangalore Workgroup -- Taken Case:{}\n".format(date,CaseStatsDic['BGLTakenVol'])
    dailyreportstring = dailyreportstring+"==================\n"
    dailyreportstring = dailyreportstring+"Onshift Engineer {}+{}\n".format(len(CaseTakenDicInclNo['BLR']),len(CaseTakenDicInclNo['BLR_Other']))
    #dailyreportstring = dailyreportstring+"BLR Queue Case {} FTS:{} P1:{} P2:{} P3:{} P4:{} UC:{}\n".format(CaseStatsDic['BGLQueueVol'],*CaseStatsDic['BGLQueueVolByPri'])
    dailyreportstring = dailyreportstring+"BLR Taken Case P1:{} P2:{} P3:{} P4:{}  --- including FTS:{}  UC:{}\n".format(*CaseStatsDic['BGLTakenVolByPri'][1:5],CaseStatsDic['BGLTakenVolByPri'][0],CaseStatsDic['BGLTakenVolByPri'][5])
    dailyreportstring = dailyreportstring+"BLR OnShift Engineer: {}\nBLR Other Engineer: {}".format(" ".join(CaseStatsDic['BGLOnShiftEngr'])," ".join(CaseStatsDic['BGLHelper']))
    
    dailyreportstring = dailyreportstring+'\n'
    
    if len(CaseStatsDic['BGLOnShiftEngr']) != 0 and False:
        dailyreportstring = dailyreportstring+"BLR Case/Engineer (TotCase/OnShift) {0:.2f}\n".format(CaseStatsDic['BGLTakenVol']/len(CaseStatsDic['BGLOnShiftEngr']))
        dailyreportstring = dailyreportstring+"BLR Case/Engineer (OnshiftEngrTakenCase/Onshift) {0:.2f}\n".format(CaseStatsDic['BGLOnShiftEngrCaseVol']/len(CaseStatsDic['BGLOnShiftEngr']))
        dailyreportstring = dailyreportstring+"BLR Case/Engineer (TotCase/(Onsfhit+Other)) {0:.2f}\n".format(CaseStatsDic['BGLTakenVol']/(len(CaseStatsDic['BGLHelper'])+len(CaseStatsDic["BGLOnShiftEngr"])))
    
    dailyreportstring = dailyreportstring+'\n'
    
    dailyreportstring = dailyreportstring+"{} Case Taken Breakdown -- APJC Total {}\n".format(date,CaseStatsDic['SydTakenVol']+CaseStatsDic['BGLTakenVol'])
    dailyreportstring = dailyreportstring+"==================\n"
    #dailyreportstring = dailyreportstring+"Onshift {} SYD:{}+{} BGL:{}+{}\n".format(\
    #    len(OnShiftEngrList),\
    #    len(CaseTakenDicInclNo['SYD']),len(CaseTakenDicInclNo['SYD_Other']),\
    #    len(CaseTakenDicInclNo['BLR']),len(CaseTakenDicInclNo['BLR_Other']))
    
    for site, site_items in CaseTakenDicInclNo.items():
        for ccoid, caselist in site_items.items():
            dailyreportstring = dailyreportstring+"{} - {} {}\n".format(site, ccoid,caselist)
        
    dailyreportstring = dailyreportstring+'\n'
    
    dailyreportstring = dailyreportstring+"{} Realtime Display -- Total:{}\n".format(date,len(InQueueEventInOrderListWithEngr))
    dailyreportstring = dailyreportstring+"==================\n"
    for case in InQueueEventInOrderListWithEngr:
        dailyreportstring = dailyreportstring+case+'\n'
    dailyreportstring = dailyreportstring+"\n"
    
    ###### List Dispatched Case ######
    dailyreportstring = dailyreportstring+"Possible Dispatched Cases\n"
    dailyreportstring = dailyreportstring+"==================\n"
    alldispatchevents = []
    furturedispatchevents = []
    for dispatchfile in dispatchcasefiles:
        with open(dispatchfile) as f:
            allevents = f.read()
        f.close()
        alldispatchevents = alldispatchevents+allevents.split("\n")
    for dispatchevent in alldispatchevents[::-1]:
        if not dispatchevent: ###### Possible emptyline at the bottomr ######
            continue 
        caseno,casesev,casetime,casetitle = dispatchevent.split('-~')
        caseno_url = '<a {} href="http://mwz.cisco.com/{}" target="_blank">{}</a>'.format('style="text-decoration:none; color:#0000FF;"',caseno,caseno)
        casedatetime = parser.parse(casetime)
        if  casedatetime >= parser.parse(date): 
            ###### Only list next 2 weeks dispatch case ######
            if parser.parse(casetime) <= parser.parse(date)+datetime.timedelta(days=14):
                furturedispatchevents.append("-~".join([caseno_url,casesev,casetime,casetitle]))
        else: ######Events in order and break when before the current date######
            break
    for event in furturedispatchevents[::-1]:
        dailyreportstring = dailyreportstring+event+"\n"
    
    dailyreportstringhtml = dailyreportstring.replace('\n','<br>\n')
    return dailyreportstringhtml

def main(date=datetime.datetime.today().strftime("%Y-%m-%d"),InQueueEventsByDate={},UpdWGAcceptEventsByDate={},CaseTakenByEngrByDate={}):
    
    ACI_InterestQueueName = ACILib.ACI_InterestQueueName
    
    current_hour = datetime.datetime.now().hour    
    shift_hour,gmt_hour = ACILib.GetShiftHour(date)

    ###### Source file only for the timestamps the tracking report is genreate at ######
    sourcefile = current_container_path + '/HTTSDashboard/logs/RabbitMQ_ACI_Event.log'
    sourcefiletime = os.path.getmtime(sourcefile)
    sourcefiledatetime = datetime.datetime.fromtimestamp(sourcefiletime) + datetime.timedelta(hours=(gmt_hour+shift_hour[0]))
    sourcefileformattime = sourcefiledatetime.strftime("%Y-%m-%d %H:%M:%S")
        
    print(InQueueEventsByDate[date])
    print(UpdWGAcceptEventsByDate[date])
    print(CaseTakenByEngrByDate[date])
    
    
if __name__ == "__main__":
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-s', action='store', dest='start_date',default=datetime.datetime.today().strftime("%Y-%m-%d"),help='Start date to generate tracking report')
    argparser.add_argument('-e', action='store', dest='end_date',default=datetime.datetime.today().strftime("%Y-%m-%d"),type=str,help='End date to generate tracking report')
    argresult = argparser.parse_args()
    
    cur_datetime = parser.parse(argresult.start_date)
    end_datetime = parser.parse(argresult.end_date)
    
    flask_container_path = ''
    current_container_path = flask_container_path
    event_path = '/HTTSDashboard/logs/ACI/events/'
    acceptfilename = current_container_path + event_path + '*_AcceptEvent.txt'
    acceptfilelist = glob.glob(acceptfilename)
    inqueuefilename = current_container_path + event_path + '*_InQueueEvent.txt'
    inqueuefilelist = glob.glob(inqueuefilename)
    
    AcceptEventsFromFile = ACILib.FindAcceptEventsFromEventFile(acceptfilelist)
    InQueueEventsFromFile = ACILib.FindInQueueEventsFromEventFile(inqueuefilelist)

    InQueueEventsByDate = ACILib.ConvertInQueueEventsByDate(start_date='2020-02-27',InQueueEventsFromFile=InQueueEventsFromFile)
    RawAcceptEventsByDate = ACILib.ConvertAcceptEventsByDate(start_date='2020-02-27',AcceptEventsFromFile=AcceptEventsFromFile) 
    UpdWGAcceptEventsByDate = ACILib.RemoveNotInQueueAcceptCase(start_date='2020-02-27',RawAcceptEventsByDate=RawAcceptEventsByDate,InQueueEventsByDate=InQueueEventsByDate)
    CaseTakenByEngrByDate = ACILib.CaseTakenByEngrGrpByDate(start_date='2020-02-27',UpdWGAcceptEventsByDate=UpdWGAcceptEventsByDate)
    
    while cur_datetime <= end_datetime:
        cur_date = cur_datetime.strftime("%Y-%m-%d")
        shift_hour,gmt_hour = ACILib.GetShiftHour(cur_date)
        print('Processing {} StartGMT {} GMT {}'.format(cur_date,shift_hour[0],gmt_hour,))
        main(cur_date,InQueueEventsByDate,UpdWGAcceptEventsByDate,CaseTakenByEngrByDate)
        cur_datetime = cur_datetime + datetime.timedelta(days=1)