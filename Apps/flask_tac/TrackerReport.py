import argparse, copy, configparser, datetime, glob, os, pathlib, re
from dateutil import parser
import ACILib

def isFindWorkgroup(shift='apjc',tech_strip='aci',site='syd',workgroup='WW-ACI-SOLUTIONS',config={}):
    
    isFoundWorkgroup = False
    
    if shift == 'apjc':
        if site == 'syd':
            syd_all_wgs = [wg.upper() for wg in config[shift]['workgroup_syd_all'].split(',')]
            TechStrip_Blr_WGs = [wg.upper() for wg in config[shift]['workgroup_{}_blr'.format(tech_strip)].split(',')]
            if any(re.search(re.compile(wg),workgroup) for wg in syd_all_wgs) and not any(re.search(re.compile(wg),workgroup) for wg in TechStrip_Blr_WGs):
            #for wg in config[shift]['workgroup_syd_all'].split(','):
            #    if re.search(re.compile(wg.upper()),workgroup.upper()):
                    #print("Found syd workgroup from Syd workgroup {} - wg {}".format(workgroup,wg))
                    isFoundWorkgroup = True
            #if not isFoundWorkgroup and re.search(r'CX-APJC-SYD',workgroup):
            #        #print("Found syd keyword workgroup from Syd workgroup {} - wg {}".format(workgroup,wg))
            #        isFoundWorkgroup = True
        if site == 'blr':
            if config[shift]['{}_{}'.format('queuemode',tech_strip)] == 'loadbalance':
                blr_wgs = config[shift]['{}_{}_blr'.format('workgroup',tech_strip)].split(',')
            else:
                blr_wgs = config[shift]['{}_{}'.format('workgroup',tech_strip)].split(',')
            for wg in blr_wgs:
                if workgroup.lower() == wg.lower():
                    isFoundWorkgroup = True
                    #print("Found blr workgroup from own workgroup {} - wg {}".format(workgroup,wg))    
    return isFoundWorkgroup
    
def GenerateCaseStatsDic(start_date='2020-06-09',end_date='2020-06-09',InQueueEventsByDate={},CaseTakenByEngrByDate={},AcceptCaseSevByDate={},InterestWorkgroup=[],shift='apjc',tech_strip='aci',config={}):
    
    '''
    InterestWorkgroup is used to generate Workgroup Stats
    tech_strip is used to generate specific Stats needed for that group
    '''
    CaseStatsByDateDic = {}
    
    start_datetime = parser.parse(start_date)
    end_datetime = parser.parse(end_date)
    cur_date = start_date
    cur_datetime = parser.parse(cur_date)
    
    while cur_datetime.date() <= end_datetime.date():
        cur_date = cur_datetime.strftime("%Y-%m-%d")
        if cur_date not in CaseStatsByDateDic.keys():
            #print("Generating CastStats Dic for date {}".format(cur_date))
            CaseStatsByDateDic[cur_date] = {}
        ###### Queue Case Volume Stats ######
        if cur_date not in InQueueEventsByDate.keys():
            cur_datetime = cur_datetime + datetime.timedelta(days=1)
            continue
        for workgroup,caselist in InQueueEventsByDate[cur_date].items():
            if workgroup == 'All' or workgroup == 'AllWithEngr' or workgroup == 'AllCases':
                continue
            #print("Date {} WG {} CaseList {}".format(cur_date,workgroup,caselist))
            if 'QueueCaseVol' not in CaseStatsByDateDic[cur_date].keys():
                CaseStatsByDateDic[cur_date]['QueueCaseVol'] = {}
            CaseStatsByDateDic[cur_date]['QueueCaseVol'][workgroup] = len(caselist)
        
        ###### Workgroup Stats ######
        ###### It differs from workgroup thus adding tech_strip to customzied it ######
        if 'WorkgroupCaseVol' not in CaseStatsByDateDic[cur_date].keys():
                CaseStatsByDateDic[cur_date]['WorkgroupCaseVol'] = {}
        if 'WorkgroupCase' not in CaseStatsByDateDic[cur_date].keys():
                CaseStatsByDateDic[cur_date]['WorkgroupCase'] = {}
        if 'WorkgroupEngrNo' not in CaseStatsByDateDic[cur_date].keys():
                CaseStatsByDateDic[cur_date]['WorkgroupEngrNo'] = {}
        if 'WorkgroupCaseVolBreakDown' not in CaseStatsByDateDic[cur_date].keys():
                CaseStatsByDateDic[cur_date]['WorkgroupCaseVolBreakDown'] = {}

        TechStrip_Pri_WGs = []
        TechStrip_CrossSkill_WGs = []
        TechStrip_Blr_WGs = []

        ##### Find Primary Workgroups of Sydney Workgroup of that tech_strip######
        ###### APJC Only: Find Pri_WG XS_WG and Onshift/Other Enginer ######
        if shift == 'apjc':
            CaseStatsByDateDic[cur_date]['SydEngrList'] = {}
            CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrList'] = []
            CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList'] = []
            CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'] = {} ####Same as CaseStatsByDateDic {'WG_Name':{'ccoid1':[caselist],'ccoid2':[caselist]}
            if config[shift]['queuemode_{}'.format(tech_strip)] == 'dedicate':
                TechStrip_Pri_WGs = config[shift]['workgroup_{}'.format(tech_strip)]
            elif config[shift]['queuemode_{}'.format(tech_strip)] == 'loadbalance':
                TechStrip_Pri_WGs = config[shift]['workgroup_{}_syd'.format(tech_strip)]
                TechStrip_Blr_WGs = [wg.upper() for wg in config[shift]['workgroup_{}_blr'.format(tech_strip)].split(',')]
            #print('Found Primary WG {} for tech_strip {}'.format(TechStrip_Pri_WGs,tech_strip))    
            TechStrip_Pri_WGs = [wg.upper() for wg in TechStrip_Pri_WGs.split(',')]
            syd_all_wgs = [wg.upper() for wg in config[shift]['workgroup_syd_all'].split(',')]
        
            for workgroup, takenlist in CaseTakenByEngrByDate[cur_date].items():
                #print("Shift:{} TechStrip:{} Workgroup:{} InterestWorkgroup:{}".format(shift,tech_strip,workgroup,InterestWorkgroup))
                #if not (workgroup.upper() in [wg.upper() for wg in InterestWorkgroup] 
                #                        or isFindWorkgroup(shift=shift,tech_strip=tech_strip,workgroup=workgroup,site='syd',config=config) 
                if not (any(re.search(re.compile(wg),workgroup) for wg in syd_all_wgs)
                                        or isFindWorkgroup(shift=shift,tech_strip=tech_strip,workgroup=workgroup,site='blr',config=config)):
                    continue
                ###### Calculate OnShift EngineeList and CrossSkill(initial) ######
                if workgroup.upper() in TechStrip_Pri_WGs:
                    #print("Primary workgroup {} takencaselist {} for tech_strip {}".format(workgroup,takenlist.keys(),tech_strip))
                    CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrList'] = CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrList'] + list(takenlist.keys())
                    #CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrNo'] = len(takenlist)
                elif any(re.search(re.compile(wg),workgroup) for wg in syd_all_wgs) and not any(re.search(re.compile(wg),workgroup) for wg in TechStrip_Blr_WGs):
                    ###### Cross-Skill logic that need to find out all Syd_Other workgroup taken the case from current tech_strip ######
                    print("Found Other_WG {} TakenList {} in SYD_ALL of strip {}".format(workgroup,takenlist,tech_strip))
                    CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'][workgroup] = takenlist
                    #print("Generating CorssSkill List WG:{} TakenList:{}".format(workgroup,CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'][workgroup]))
                    ###### Remove Other Engineer List here as it's been calculated after CrossSkill calculation ######
                    #CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList'] = CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList'] + list(takenlist.keys())

            ###### Remove the Case which is not on InQueueEventsByDate[cur_date]['AllCases'] list case and remaining are the Cross-Skill case ######
            removelist = {}
            #print("XSkill List {}".format(CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill']))
            for wg,takenlist in CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'].items():
                removelist[wg] = {}
                for ccoid,takenlist_1 in takenlist.items():
                    removelist[wg][ccoid] = []
                    removelist[wg][ccoid] = [caseno for caseno in takenlist_1 if caseno not in InQueueEventsByDate[cur_date]['AllCases']]
            #print("NotInQueueCaseList {}".format(removelist))
            for wg, ccoid_case_list in removelist.items():
                for ccoid, caselist in ccoid_case_list.items():
                    for case in caselist:
                        CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'][wg][ccoid].remove(case)
                    if len(CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'][wg][ccoid]) == 0:
                        del CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'][wg][ccoid]
                if len(CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'][wg]) == 0:
                       del CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'][wg]
            print("XSkill List after removal {}".format(CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill']))
            for wg in CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'].keys():
                TechStrip_CrossSkill_WGs.append(wg)
            ###### Calculate Other ENgineer list here based on the CrossSkill Result ######
            for wg, ccoid_case_list in CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'].items():
                CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList'] = CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList'] + list(ccoid_case_list.keys())
            ###### Sorted by alphabet ######
            CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrList'] = sorted(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrList'])
            CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList'] = sorted(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList'])
            #print("Syd: Onshift {} Other".format(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrList'],CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList']))
        
        ###### Workgroup Statistics based on the Pri_WGs and CrossSkill_WGs ######
        for workgroup, takenlist in CaseTakenByEngrByDate[cur_date].items():
            #print("Shift:{} TechStrip:{} Workgroup:{} InterestWorkgroup:{}".format(shift,tech_strip,workgroup,InterestWorkgroup))
            #if shift == 'apjc' and not (workgroup.upper() in [wg.upper() for wg in InterestWorkgroup] 
            #                            or isFindWorkgroup(shift=shift,tech_strip=tech_strip,workgroup=workgroup,site='syd',config=config) 
            #                            or isFindWorkgroup(shift=shift,tech_strip=tech_strip,workgroup=workgroup,site='blr',config=config)):
            #    continue
            ###### TODO: Testing the PriWGs and CrokssSkill Filter ######
            if shift == 'apjc':
                if not (workgroup.upper() in TechStrip_Pri_WGs or workgroup.upper() in TechStrip_Blr_WGs
                or workgroup.upper() in [wg.upper() for wg in CaseStatsByDateDic[cur_date]['SydEngrList']['CrossSkill'].keys()]):
                    continue
            elif shift == 'emea' and not workgroup.upper() in [wg.upper() for wg in InterestWorkgroup]:
                continue
            
            #print("Hitting WG {} - {}".format(workgroup,takenlist))
            CaseStatsByDateDic[cur_date]['WorkgroupCase'][workgroup] = {}
            CaseStatsByDateDic[cur_date]['WorkgroupCase'][workgroup] = takenlist
            CaseStatsByDateDic[cur_date]['WorkgroupEngrNo'][workgroup] = len(takenlist)
            
            ###### Calculate workgroup case volume ######
            #print("WG {} Values {}".format(workgroup,CaseTakenByEngrByDate[cur_date][workgroup]))
            workgroup_caselist = CaseTakenByEngrByDate[cur_date][workgroup].values()
            workgroup_caselist = [case for cases in workgroup_caselist for case in cases]
            #print("WG {} CaseVolume {}".format(workgroup,workgroup_caselist))
            CaseStatsByDateDic[cur_date]['WorkgroupCaseVol'][workgroup] = len(workgroup_caselist)
            
            ###### Calculate workgroup case volume BreakDown P0,P1,P2,P3,P4######
            for case in workgroup_caselist:
                for sev,caselist in AcceptCaseSevByDate[cur_date].items():
                    if case in caselist:
                        #print("Date {} Case {} Sev {}".format(cur_date,case,sev))
                        if workgroup not in CaseStatsByDateDic[cur_date]['WorkgroupCaseVolBreakDown']:
                            CaseStatsByDateDic[cur_date]['WorkgroupCaseVolBreakDown'][workgroup] = [0,0,0,0,0]
                        CaseStatsByDateDic[cur_date]['WorkgroupCaseVolBreakDown'][workgroup][int(sev)] = CaseStatsByDateDic[cur_date]['WorkgroupCaseVolBreakDown'][workgroup][int(sev)]+1
        
        ###### It must before the LB Volume Calculation ######
        CaseStatsByDateDic[cur_date]['WorkgroupCaseVol']['Total'] = sum(CaseStatsByDateDic[cur_date]['WorkgroupCaseVol'].values())
        
        ###### Loadbalance Queue Case Volume ######
        if shift == 'apjc':
            if config[shift]['{}_{}'.format('queuemode',tech_strip)] == 'loadbalance':
                SYDCaseVol,BLRCaseVol = 0,0
                for workgroup, casevol in CaseStatsByDateDic[cur_date]['WorkgroupCaseVol'].items():
                    #print("WG {} CaseVolume {}".format(workgroup,casevol))
                    if isFindWorkgroup(shift=shift,tech_strip=tech_strip,workgroup=workgroup,site='syd',config=config):
                        SYDCaseVol = SYDCaseVol + casevol
                    elif isFindWorkgroup(shift=shift,tech_strip=tech_strip,workgroup=workgroup,site='blr',config=config):
                        BLRCaseVol = BLRCaseVol + casevol
                CaseStatsByDateDic[cur_date]['WorkgroupCaseVol']['SYDCaseVol'] = SYDCaseVol
                CaseStatsByDateDic[cur_date]['WorkgroupCaseVol']['BLRCaseVol'] = BLRCaseVol
                
        #print(CaseStatsByDateDic[cur_date])
        cur_datetime = cur_datetime + datetime.timedelta(days=1)
        
    return CaseStatsByDateDic

def MakeHTMLTrackerReport(start_date='2020-06-09',end_date='2020-06-09',InQueueEventsByDate={},CaseTakenByEngrByDate={},CaseStatsByDateDic={},DispatchEvents=[],shift='apjc',tech_strip='aci',config={}):
    '''
    Generate Deaily HTML Report
    '''
    
    start_datetime = parser.parse(start_date)
    end_datetime = parser.parse(end_date)
    cur_date = start_date
    cur_datetime = parser.parse(cur_date)
    HTMLTrackingReport = {}

    QueueName = config[shift]['_'.join(['queuename',tech_strip.upper()])].split(',')
    QueueName = [qn.upper() for qn in QueueName]
        
    while cur_datetime.date() <= end_datetime.date():
        
        cur_date = cur_datetime.strftime("%Y-%m-%d")
        if cur_date not in InQueueEventsByDate.keys() or cur_date not in CaseTakenByEngrByDate or cur_date not in CaseStatsByDateDic:
            HTMLTrackingReport[cur_date] = '{} {} {} No Event. <br> Possible Reason: <br>1.Shift has not started or just started.<br>2. BDB is down.'.format(cur_date,shift.upper(),tech_strip.upper(),)
            cur_datetime = cur_datetime + datetime.timedelta(days=1)
            continue
        
        ###### Start Generating the Daily HTML Report ######
        
        #print(InQueueEventsByDate[cur_date])
        #print("MakeHTMLTrackerReport CaseTakenByEngrByDate {}\n".format(CaseTakenByEngrByDate[cur_date]))
        #print("MakeHTMLTrackerReport CaseStatsByDateDic {}\n".format(CaseStatsByDateDic[cur_date]))
        
        if shift == 'apjc':
            dailyreportstring = "{} Queue Case Volume -- Total {} *** Update at(AEST/AEDT): {}\n".format(cur_date, sum(CaseStatsByDateDic[cur_date]['QueueCaseVol'].values()),CaseStatsByDateDic['UpdateTime'])
        elif shift == 'emea':
            dailyreportstring = "{} Queue Case Volume -- Total {} *** Update at(IST): {}\n".format(cur_date, sum(CaseStatsByDateDic[cur_date]['QueueCaseVol'].values()),CaseStatsByDateDic['UpdateTime'])
            
        dailyreportstring = dailyreportstring+"==================\n"
        for queue, volume in CaseStatsByDateDic[cur_date]['QueueCaseVol'].items():
            dailyreportstring = dailyreportstring+"{}:{}\n".format(queue,volume)
        dailyreportstring = dailyreportstring+'\n'
        
        if shift == 'apjc':
            if config[shift]['{}_{}'.format('queuemode',tech_strip)] == 'loadbalance': ##### loadbalance report#####
                
                dailyreportstring = dailyreportstring+"{} Sydney SR ownership taken by workgroup - {} cases \n".format(cur_date,CaseStatsByDateDic[cur_date]['WorkgroupCaseVol']['SYDCaseVol'])
                dailyreportstring = dailyreportstring+"==================\n"
                
                dailyreportstring = dailyreportstring+"OnShift Engineer({}): {}\n".format(len(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrList']),
                                                                                          ', '.join(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrList']))
                dailyreportstring = dailyreportstring+"Other Engineer({}): {}\n\n".format(len(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList']),
                                                                                          ', '.join(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList']))

                for workgroup,engrcasettakenlist in CaseStatsByDateDic[cur_date]['WorkgroupCase'].items():
                    if not isFindWorkgroup(shift=shift,tech_strip=tech_strip,workgroup=workgroup,site='syd',config=config):
                        continue
                    dailyreportstring = dailyreportstring + "WORKGROUP {} - {} engineers {} cases\n".format(workgroup,CaseStatsByDateDic[cur_date]['WorkgroupEngrNo'][workgroup],CaseStatsByDateDic[cur_date]['WorkgroupCaseVol'][workgroup])
                    dailyreportstring = dailyreportstring + "Case Taken by Severity P1:{} P2:{} P3:{} P4:{}\n".format(*CaseStatsByDateDic[cur_date]['WorkgroupCaseVolBreakDown'][workgroup][1:])
                    for engr, caselist in engrcasettakenlist.items():
                        #print("Engr {} CaseSum {} CaseList {}".format(engr,len(caselist),caselist))
                        dailyreportstring = dailyreportstring+"{} {} {}\n".format(engr,len(caselist),caselist)
                    dailyreportstring = dailyreportstring+"\n"
                    
                dailyreportstring = dailyreportstring+"{} Bangalore SR ownership taken by workgroup - {} cases \n".format(cur_date,CaseStatsByDateDic[cur_date]['WorkgroupCaseVol']['BLRCaseVol'])
                dailyreportstring = dailyreportstring+"==================\n"
                for workgroup,engrcasettakenlist in CaseStatsByDateDic[cur_date]['WorkgroupCase'].items():
                    #print("WG {} EngrTakenCaseList {} ".format(workgroup,engrcasettakenlist))
                    if not isFindWorkgroup(shift=shift,tech_strip=tech_strip,workgroup=workgroup,site='blr',config=config):
                        continue
                    dailyreportstring = dailyreportstring + "WORKGROUP {} - {} engineers {} cases\n".format(workgroup,CaseStatsByDateDic[cur_date]['WorkgroupEngrNo'][workgroup],CaseStatsByDateDic[cur_date]['WorkgroupCaseVol'][workgroup])
                    dailyreportstring = dailyreportstring + "Case Taken by Severity P1:{} P2:{} P3:{} P4:{}\n".format(*CaseStatsByDateDic[cur_date]['WorkgroupCaseVolBreakDown'][workgroup][1:])
                    for engr, caselist in engrcasettakenlist.items():
                        #print("Engr {} CaseSum {} CaseList {}".format(engr,len(caselist),caselist))
                        dailyreportstring = dailyreportstring+"{} {} {}\n".format(engr,len(caselist),caselist)
                    dailyreportstring = dailyreportstring+"\n"
                    
            else:
                
                dailyreportstring = dailyreportstring+"{} SR ownership taken by workgroup - {} cases \n".format(cur_date,CaseStatsByDateDic[cur_date]['WorkgroupCaseVol']['Total'])
                dailyreportstring = dailyreportstring+"==================\n"
                dailyreportstring = dailyreportstring+"OnShift Engineer({}): {}\n".format(len(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrList']),
                                                                                          ', '.join(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOnShiftEngrList']))
                dailyreportstring = dailyreportstring+"Other Engineer({}): {}\n\n".format(len(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList']),
                                                                                          ', '.join(CaseStatsByDateDic[cur_date]['SydEngrList']['SydOtherEngrList']))
                for workgroup,engrcasettakenlist in CaseStatsByDateDic[cur_date]['WorkgroupCase'].items():
                    #print("WG {} EngrTakenCaseList {} ".format(workgroup,engrcasettakenlist))
                    dailyreportstring = dailyreportstring + "WORKGROUP {} - {} engineers {} cases\n".format(workgroup,CaseStatsByDateDic[cur_date]['WorkgroupEngrNo'][workgroup],CaseStatsByDateDic[cur_date]['WorkgroupCaseVol'][workgroup])
                    dailyreportstring = dailyreportstring + "Case Taken by Severity P1:{} P2:{} P3:{} P4:{}\n".format(*CaseStatsByDateDic[cur_date]['WorkgroupCaseVolBreakDown'][workgroup][1:])
                    for engr, caselist in engrcasettakenlist.items():
                        #print("Engr {} CaseSum {} CaseList {}".format(engr,len(caselist),caselist))
                        dailyreportstring = dailyreportstring+"{} {} {}\n".format(engr,len(caselist),caselist)
                    dailyreportstring = dailyreportstring+"\n"
                    
        elif shift == 'emea':
            
            dailyreportstring = dailyreportstring+"{} SR ownership taken by workgroup - {} cases.\n".format(cur_date,CaseStatsByDateDic[cur_date]['WorkgroupCaseVol']['Total'])
            dailyreportstring = dailyreportstring+"==================\n"
            for workgroup,engrcasettakenlist in CaseStatsByDateDic[cur_date]['WorkgroupCase'].items():
                #print("WG {} EngrTakenCaseList {} ".format(workgroup,engrcasettakenlist))
                dailyreportstring = dailyreportstring + "WORKGROUP {} - {} engineers {} cases\n".format(workgroup,CaseStatsByDateDic[cur_date]['WorkgroupEngrNo'][workgroup],CaseStatsByDateDic[cur_date]['WorkgroupCaseVol'][workgroup])
                dailyreportstring = dailyreportstring + "Case Taken by Severity P1:{} P2:{} P3:{} P4:{}\n".format(*CaseStatsByDateDic[cur_date]['WorkgroupCaseVolBreakDown'][workgroup][1:])
                for engr, caselist in engrcasettakenlist.items():
                    #print("Engr {} CaseSum {} CaseList {}".format(engr,len(caselist),caselist))
                    dailyreportstring = dailyreportstring+"{} {} {}\n".format(engr,len(caselist),caselist)
                dailyreportstring = dailyreportstring+"\n"
                
        #dailyreportstring = dailyreportstring+"\n"
        dailyreportstring = dailyreportstring+"{} Realtime events - Total Cases(incl. FTS/UC): {}\n Queue: {} \n".format(cur_date,sum(CaseStatsByDateDic[cur_date]['QueueCaseVol'].values()),", ".join(QueueName))
        dailyreportstring = dailyreportstring+"==================\n"
        dailyreportstring = dailyreportstring+"\n".join(InQueueEventsByDate[cur_date]['AllWithEngr'])
        dailyreportstring = dailyreportstring+"\n\n"
        
        ###### List Dispatched Case ######
        dailyreportstring = dailyreportstring+"Possible dispatched cases - next 14 days\n"
        dailyreportstring = dailyreportstring+"==================\n"
        furturedispatchevents = []
        for dispatchevent in DispatchEvents[::-1]:
            if not dispatchevent: ###### Possible emptyline at the bottomr ######
                continue 
            #print("Dispatch event {}".format(dispatchevent))
            caseno,casesev,casetime,casetitle = dispatchevent.split('-~')
            caseno_url = '<a {} href="http://mwz.cisco.com/{}" target="_blank">{}</a>'.format('style="text-decoration:none; color:#0000FF;"',caseno,caseno)
            casedatetime = parser.parse(casetime)
            if  casedatetime >= parser.parse(cur_date): 
                ###### Only list next 2 weeks dispatch case ######
                if parser.parse(casetime) <= parser.parse(cur_date)+datetime.timedelta(days=14):
                    furturedispatchevents.append("-~".join([caseno_url,casesev,casetime,casetitle]))
            else: ######Events in order and break when before the current date######
                break
        for event in furturedispatchevents[::-1]:
            dailyreportstring = dailyreportstring+event+"\n"
        
        #print(dailyreportstring)
        cur_datetime = cur_datetime + datetime.timedelta(days=1)
        dailyreportstringhtml = dailyreportstring.replace('\n','<br>\n')
        HTMLTrackingReport[cur_date] = dailyreportstringhtml
        
    return HTMLTrackingReport

def main(date=datetime.datetime.today().strftime("%Y-%m-%d"),InQueueEventsByDate={},CaseTakenByEngrByDate={},CaseStatsByDateDic={},DispatchEvents={},shift='apjc',tech_strip='aci',config={}):
    
    current_hour = datetime.datetime.now().hour    
    shift_hour,gmt_hour = ACILib.GetShiftHour(date)

    ###### Source file only for the timestamps the tracking report is genreate at ######
    sourcefile = current_container_path + '/HTTSDashboard/logs/RabbitMQ_ACI_Event.log'
    sourcefiletime = os.path.getmtime(sourcefile)
    sourcefiledatetime = datetime.datetime.fromtimestamp(sourcefiletime) + datetime.timedelta(hours=(gmt_hour+shift_hour[0]))
    sourcefileformattime = sourcefiledatetime.strftime("%Y-%m-%d %H:%M:%S")
    
    #### The following is used to generate HTML report every day ######
    #print(InQueueEventsByDate[date])
    #print("CaseTakenByEngrByDate in TrackerReport {}".format(CaseTakenByEngrByDate[date]))
    #print("CaseStatsByDateDic in TrackerReport {}".format(CaseStatsByDateDic[date]))
    
    reportpath = config[shift]['_'.join(['reportpath',tech_strip.upper()])]
    HTMLTrackingReport = MakeHTMLTrackerReport(start_date=date,end_date=date,InQueueEventsByDate=InQueueEventsByDate,CaseTakenByEngrByDate=CaseTakenByEngrByDate,CaseStatsByDateDic=CaseStatsByDateDic,DispatchEvents=DispatchEvents,shift=shift,tech_strip=tech_strip,config=config)
    
    pathlib.Path(reportpath).mkdir(parents=True, mode=775,exist_ok=True)
    for date,htmlreport in HTMLTrackingReport.items():
        filename = "{}{}_{}_{}.html".format(reportpath,date,shift.upper(),tech_strip.upper())
        with open(filename, 'w') as file:
            file.write(htmlreport)

if __name__ == "__main__":
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-s', action='store', dest='start_date',default=datetime.datetime.today().strftime("%Y-%m-%d"),help='Start date to generate tracking report')
    argparser.add_argument('-e', action='store', dest='end_date'  ,default=datetime.datetime.today().strftime("%Y-%m-%d"),type=str,help='End date to generate tracking report')
    argparser.add_argument('-p', action='store', dest='shift',default='apjc',type=str,help='Shift:apjc|emea')
    argresult = argparser.parse_args()
    shift = argresult.shift
    start_date = argresult.start_date
    end_date = argresult.end_date
    
    #Reading current config from file
    #Docker WORKDIR is /HTTSDashboard/Apps/
    config = configparser.ConfigParser()
    config.read('./flask_tac/tacconfig.ini')
    tech_strip_list =  config[shift]['tech_strips'].split(',')
    start_datetime = parser.parse(start_date)
    end_datetime = parser.parse(end_date)
    
    for tech_strip in tech_strip_list:
        
        CaseStatsByDateDic = {}
        UpdateTime = ''
        
        event_path = config[shift]['_'.join(['eventpath',tech_strip.upper()])]
        InterestWorkgroup = config[shift]['_'.join(['workgroup',tech_strip.upper()])].split(',')

        flask_container_path = ''
        current_container_path = flask_container_path
        acceptfilename = current_container_path + event_path + '*_AcceptEvent.txt'
        acceptfilelist = glob.glob(acceptfilename)
        inqueuefilename = current_container_path + event_path + '*_InQueueEvent.txt'
        inqueuefilelist = glob.glob(inqueuefilename)
        dispatchfilename = current_container_path + event_path + '*_DispatchedEvent.txt'
        dispatchfilelist = glob.glob(dispatchfilename)        
        DispatchEvents = []
        for dispatchfile in dispatchfilelist:
            #print("TechStrip {} Reading Dispatch file {}".format(tech_strip,dispatchfile))
            with open(dispatchfile) as f:
                allevents = f.read()
            f.close()
        DispatchEvents = DispatchEvents+allevents.split("\n")
        
        UpdateTime,InQueueEventsFromFile = ACILib.FindInQueueEventsFromEventFile(inqueuefilelist)
        AcceptEventsFromFile = ACILib.FindAcceptEventsFromEventFile(acceptfilelist)

        _, UpdateTime = ACILib.isOnShift(timestamp=UpdateTime,timezone = 'GMT',shift=shift,debug=False)
        #print("Tracker Report UpdateTime {} Shift {}".format(UpdateTime,shift))
        
        InQueueEventsByDate = ACILib.ConvertInQueueEventsByDate(start_date=start_date,InQueueEventsFromFile=InQueueEventsFromFile)
        RawAcceptEventsByDate,AcceptCaseSevByDate = ACILib.ConvertAcceptEventsByDate(AcceptEventsFromFile=AcceptEventsFromFile)
        
        #print(RawAcceptEventsByDate['2020-06-17'])
        InQueueEventsByDate = ACILib.UpdWithEngrConvertInQueueEventsByDate(start_date=start_date,end_date=end_date,shift=shift,RawAcceptEventsByDate=RawAcceptEventsByDate,InQueueEventsByDate=InQueueEventsByDate)
        CaseTakenByEngrByDate = ACILib.CaseTakenByEngrGrpByDate(start_date=start_date,end_date=end_date,RawAcceptEventsByDate=RawAcceptEventsByDate)
        #print("CaseTakenByEngrByDate {}".format(CaseTakenByEngrByDate['2020-06-17']))
        CaseStatsByDateDic = GenerateCaseStatsDic(start_date=start_date,end_date=end_date,InQueueEventsByDate=InQueueEventsByDate,CaseTakenByEngrByDate=CaseTakenByEngrByDate,AcceptCaseSevByDate=AcceptCaseSevByDate,InterestWorkgroup=InterestWorkgroup,shift=shift,tech_strip=tech_strip,config=config)
        CaseStatsByDateDic['UpdateTime'] = UpdateTime
        print("Generating TrackerReport:Shift:{} TechStrip:{} UpdTime:{}\nInQueueFilename:{}\nAcceptFilename:{}".format(shift,tech_strip,CaseStatsByDateDic['UpdateTime'],inqueuefilename,acceptfilename))
        
        cur_datetime = parser.parse(start_date)
        while cur_datetime <= end_datetime:
            
            cur_date = cur_datetime.strftime("%Y-%m-%d")
            shift_hour,gmt_hour = ACILib.GetShiftHour(cur_date,shift=shift)
            print('Processing shift {} {} StartGMT {} GMT {}'.format(shift, cur_date,shift_hour[0],gmt_hour,))

            main(cur_date,InQueueEventsByDate,CaseTakenByEngrByDate,CaseStatsByDateDic,DispatchEvents,shift,tech_strip,config)
            cur_datetime = cur_datetime + datetime.timedelta(days=1)