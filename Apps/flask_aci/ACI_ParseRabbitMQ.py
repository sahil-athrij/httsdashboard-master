import dateutil
from dateutil import parser
import datetime , re, os, argparse, glob
import ACILib

#It was exected in the jupyter notebook container , path is different from flask container.

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

def main(date = datetime.datetime.today().strftime("%Y-%m-%d")):
    
    current_hour = datetime.datetime.now().hour    
    shift_hour,gmt_hour = ACILib.GetShiftHour(date)
    
    flask_container_path = ''
    current_container_path = flask_container_path
    sourcefile = current_container_path + '/HTTSDashboard/logs/RabbitMQ_ACI_Event.log'
    sourcefiletime = os.path.getmtime(sourcefile)
    sourcefiledatetime = datetime.datetime.fromtimestamp(sourcefiletime) + datetime.timedelta(hours=(gmt_hour+shift_hour[0]))
    sourcefileformattime = sourcefiledatetime.strftime("%Y-%m-%d %H:%M:%S")
    
    dispatchcasefiles = glob.glob(current_container_path+'/HTTSDashboard/logs/ACI/events/*DispatchedEvent.txt')
    commentfile = current_container_path + '/HTTSDashboard/logs/ACI/html/comment.txt'
    dailyreportfiledir = current_container_path + '/HTTSDashboard/logs/ACI/report/'
    dailyreportfilename = date+'.html'
    dailyreportstring = ""
    
    ACI_SYDEngrList = ACILib.ACI_SYDEngrList
    ACI_BGLEngrList = ACILib.ACI_BGLEngrList
    ACI_BGLOtherEngrList = ACILib.ACI_BGLOtherEngrList
    ACI_SYDOtherEngrList = ACILib.ACI_SYDOtherEngrList
    ACI_InterestQueueName = ACILib.ACI_InterestQueueName
    
    CSSEngrList = []
    OnShiftEngrList = []
    InQueueEventInOrderListWithEngr = []
    
    CaseQty = {'CX-APJC-BLR-ACI-SSPT':0,
               'WW-ACI-Solutions':0,
               'CX-APJC-SYD-ACI-SSPT':0,
               'WW-Rakuten-ACI':0,
               'FTS':0,'UC':0}
    CaseTakenDic = {}
    CaseTakenDicInclNo = {'SYD':{},'SYD_Other':{},'BLR':{},'BLR_Other':{}}
    CaseTakenByEngrDic = {}
    CaseStatsDic = {"SydQueueVol":0,"BGLQueueVol":0,
                "SydTakenVol":0,"BGLTakenVol":0,
                'FTSCaseVol':0,'UCCaseVol':0,
                "SydQueueVolByPri":[0,0,0,0,0,0],"BGLQueueVolByPri":[0,0,0,0,0,0], #0 FTS #1,2,3,4 Priority #5 Urgent Collab
                "SydTakenVolByPri":[0,0,0,0,0,0],"BGLTakenVolByPri":[0,0,0,0,0,0], #0 FTS #1,2,3,4 Priority #5 Urgent Collab
                "SydOnShiftEngr":1,"BGLOnShiftEngr":1,
                "SydOnShiftEngrTakenVol":0,"BGLOnShiftEngrTakenVol":1,
                "SYDHelper":0,"BGLHelper":0,
                }
    
    with open(sourcefile) as f:
        allevents = f.read()
    f.close()
    allevents = allevents.split("\n")

    allevents_in_date = ACILib.GetRawEventsFromDate(allevents,date=date,shift_start_hour=shift_hour[0],shift_end_hour=shift_hour[1],debug=False)
    #print("{} There are {} raw events".format(date,len(allevents_in_date)))

    InQueueEventList = ACILib.FindInQueueEvent(allevents_in_date,InterestQueueName=ACI_InterestQueueName,shift_start_hour=shift_hour[0],shift_end_hour=shift_hour[1],debug=False)
    #print("{} There are {} inqueue event in date".format(date,len(InQueueEventList)))
    
    InQueueEventInOrderList = ACILib.SortInQueueEventByTime(InQueueEventList,date=date,debug=False)
    CaseStatsDic = ACILib.GetStatsFromInQueueEventInOrderList(InQueueEventInOrderList,CaseStatsDic)
    
    #print("{} Sorting inqueue event in order by time {} events... done".format(date, len(InQueueEventInOrderList)))

    #for case in InQueueEventInOrderList:
    #    print(case)

    for case in InQueueEventInOrderList:
        if case.split("-~")[2] == 'FTS':
            CaseQty['FTS'] = CaseQty['FTS'] + 1
        elif case.split("-~")[2] == 'UC':
            CaseQty['UC'] = CaseQty['UC'] + 1
        elif case.split("-~")[2] == 'CX-APJC-SYD-ACI-SSPT':
            CaseQty['CX-APJC-SYD-ACI-SSPT'] = CaseQty['CX-APJC-SYD-ACI-SSPT'] + 1
        elif case.split("-~")[2] == 'CX-APJC-BLR-ACI-SSPT':
            CaseQty['CX-APJC-BLR-ACI-SSPT'] = CaseQty['CX-APJC-BLR-ACI-SSPT'] + 1
        elif case.split("-~")[2] == 'WW-ACI-Solutions':
            CaseQty['WW-ACI-Solutions'] = CaseQty['WW-ACI-Solutions'] + 1
        elif case.split("-~")[2] == 'WW-Rakuten-ACI':
            CaseQty['WW-Rakuten-ACI'] = CaseQty['WW-Rakuten-ACI'] + 1
    
    AcceptEventInOrderList = ACILib.CaseAcceptInOrderByTime(allevents_in_date,date=date,debug=False)
    ACI_SYDEngrList,ACI_SYDOtherEngrList,ACI_BGLEngrList,ACI_BGLOtherEngrList = ACILib.UpdateEngrListFromAcceptEventInOrderList(AcceptEventInOrderList,[ACI_SYDEngrList,ACI_SYDOtherEngrList,ACI_BGLEngrList,ACI_BGLOtherEngrList],WKGroupList=['APT-ACI-SOLUTIONS','APT-ACI-SOLUTIONS2'])
        
    CaseStatsDic = ACILib.GetStatsFromCaseAcceptInOrderByTime(AcceptEventInOrderList,CaseStatsDic,[ACI_SYDEngrList,ACI_SYDOtherEngrList,ACI_BGLEngrList,ACI_BGLOtherEngrList])
    
    #print("{} Sorting accept event in order by time {} events ... done".format(date,len(AcceptEventInOrderList)))

    for case in AcceptEventInOrderList:
        #print(case)
        caseno,severity,ccoid,workgroup,time = case.split("-~")
        if ccoid not in CaseTakenDic.keys():
            CaseTakenDic[ccoid] = []
        if caseno not in CaseTakenDic[ccoid]:
            CaseTakenDic[ccoid].append(caseno)
            
        if ccoid not in OnShiftEngrList and (ccoid in ACI_SYDEngrList or ccoid in ACI_BGLEngrList 
                                             or ccoid in ACI_BGLOtherEngrList or ccoid in ACI_SYDOtherEngrList):
            OnShiftEngrList.append(ccoid)
        if caseno not in CaseTakenByEngrDic.keys():
            CaseTakenByEngrDic[caseno] = []
            
        if ccoid in ACI_SYDEngrList or ccoid in ACI_SYDOtherEngrList:
            CaseStatsDic['SydTakenVolByPri'][int(severity)] = CaseStatsDic['SydTakenVolByPri'][int(severity)] + 1
            CaseTakenByEngrDic[caseno].append(ccoid+"(SYD)")
        elif ccoid in ACI_BGLEngrList or ccoid in ACI_BGLOtherEngrList:
            CaseStatsDic['BGLTakenVolByPri'][int(severity)] = CaseStatsDic['BGLTakenVolByPri'][int(severity)] + 1
            CaseTakenByEngrDic[caseno].append(ccoid+"(BLR)")
        elif ccoid == 'lowtouch':
            CaseTakenByEngrDic[caseno].append(ccoid+"(HW)")
        else:
            CaseTakenByEngrDic[caseno].append(ccoid+"(Unknown)")
    
    for ccoid, caselist in CaseTakenDic.items():
        if ccoid in ACI_SYDEngrList:
            CaseTakenDicInclNo['SYD'][ccoid] = list([len(caselist),*caselist])
        elif ccoid in ACI_SYDOtherEngrList:
            CaseTakenDicInclNo['SYD_Other'][ccoid] = list([len(caselist),*caselist])
        elif ccoid in ACI_BGLEngrList:
            CaseTakenDicInclNo['BLR'][ccoid] = list([len(caselist),*caselist])
        elif ccoid in ACI_BGLOtherEngrList:
            CaseTakenDicInclNo['BLR_Other'][ccoid] = list([len(caselist),*caselist])
    
    InQueueEventInOrderListWithEngr = []
    for caseline in InQueueEventInOrderList:
        caseno,priority,queue,timestamp = caseline.split("-~")
        ###### CaseStatsDic FTS Stats ######
        if queue == 'FTS':
            for ccoid,caselist in CaseTakenDic.items():
                if caseno in caselist:
                    if ccoid in ACI_SYDEngrList or ccoid in ACI_SYDOtherEngrList:
                        CaseStatsDic['SydTakenVolByPri'][0] = CaseStatsDic['SydTakenVolByPri'][0] + 1
                    elif ccoid in ACI_BGLEngrList or ccoid in ACI_BGLOtherEngrList:
                        CaseStatsDic['BGLTakenVolByPri'][0] = CaseStatsDic['BGLTakenVolByPri'][0] + 1
        
        ###### CaseStatsDic UC Stats ######
        elif queue == 'UC':
            for ccoid,caselist in CaseTakenDic.items():
                if caseno in caselist:
                    if ccoid in ACI_SYDEngrList or ccoid in ACI_SYDOtherEngrList:
                        CaseStatsDic['SydTakenVolByPri'][5] = CaseStatsDic['SydTakenVolByPri'][5] + 1
                    elif ccoid in ACI_BGLEngrList or ccoid in ACI_BGLOtherEngrList:
                        CaseStatsDic['BGLTakenVolByPri'][5] = CaseStatsDic['BGLTakenVolByPri'][5] + 1   
        
        #print("GMT {} StartGMT {}".format(gmt_hour,shift_hour[0]),parser.parse(timestamp).strftime("%Y-%m-%d %H:%M:%S"))
        caseno_url = '<a {} href="http://mwz.cisco.com/{}" target="_blank">{}</a>'.format('style="text-decoration:none; color:#0000FF;"',caseno,caseno)
        if caseno in CaseTakenByEngrDic.keys():
            InQueueEventInOrderListWithEngr.append(caseno_url+'-~'+priority+"-~"+queue+'-~'+
                                               (parser.parse(timestamp)+datetime.timedelta(hours=gmt_hour)).strftime("%Y-%m-%d %H:%M:%S")+
                                               '-~'+"-~".join(CaseTakenByEngrDic[caseno]))
        else:
            InQueueEventInOrderListWithEngr.append(caseno_url+'-~'+priority+"-~"+queue+'-~'+
                                               (parser.parse(timestamp)+datetime.timedelta(hours=gmt_hour)).strftime("%Y-%m-%d %H:%M:%S")
                                               )
    
    ###### Calcuate Cases Taken by WG ######
    #No Need to count as it's been in severity count above
    CaseStatsDic['SydTakenVol'] = sum(CaseStatsDic['SydTakenVolByPri'][1:5])
    CaseStatsDic['BGLTakenVol'] = sum(CaseStatsDic['BGLTakenVolByPri'][1:5])
    
    dailyreportstringhtml =  GenerateHTMLfile(date,sourcefileformattime,dispatchcasefiles,CaseQty,CaseStatsDic,OnShiftEngrList,CaseTakenDicInclNo,InQueueEventInOrderListWithEngr)

    with open(dailyreportfiledir+dailyreportfilename, 'w') as file:
        file.write(dailyreportstringhtml)
        
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