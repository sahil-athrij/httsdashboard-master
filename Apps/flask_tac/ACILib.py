import copy, dateutil, datetime, re, pytz
from dateutil import parser

######Function List #######
#  GetShiftHour(date='2020-04-05') #Input:StringDate Return:ShiftStartHour, StartGMT
#  isOnShift(timestamp = '2020-03-27 18:00:00',timezone = 'America/Los_Angeles') #Input:Timestamp,TZ Return:True or False

ACI_SYDEngrList = ['tonzeng', 'minkwong', 'wilchong', 'debabbar', 'lindawa', 'junwa', 'siddhp']
ACI_SYDOtherEngrList = ['zdazhi', 'zmeng']
ACI_BGLEngrList = ['deepaky', 'jawalia', 'maveer', 'raghb', 'shparanj', 'vkalmath', 'hethakur', 'gauvasud', 'kahande',
                   'prpratee', 'reperuma', 'roagraw2']
ACI_BGLOtherEngrList = ['amikum', 'anirukas', 'deepakba', 'bharatkc', 'kdoodi', 'visgupt2', 'knagavol']
ACI_InterestQueueName = ['WW-ACI-Solutions', 'CX-APJC-BLR-ACI-SSPT', 'CX-APJC-SYD-ACI-SSPT', 'WW-Rakuten-ACI']


def AddAcceptEventByDateFromFile(date, AddList, AcceptEvents):
    if not AcceptEvents:
        AcceptEvents = {}
    if parser.parse(date).year not in AcceptEvents.keys():
        AcceptEvents[parser.parse(date).year] = []
    ######Need to deep copy the list ######
    AddedDateAcceptEvents = copy.deepcopy(AcceptEvents)
    insert_index = len(AcceptEvents[parser.parse(date).year])

    for year, events in AcceptEvents.items():
        for index, event in enumerate(events[::-1]):
            caseno, severity, ccoid, workgroup, casetime = event.split('-~')
            # print(event.strip())
            if parser.parse(casetime).date() < parser.parse(date).date():
                # print("Insert Index Found {}-{} {}".format(parser.parse(casetime).date(),parser.parse(date).date(),insert_index))
                insert_index = index
                break
        insert_index = len(AddedDateAcceptEvents[year]) - insert_index
        # print("Insert Index {}".format(insert_index))
        # print(AcceptEvents[year][insert_index])

        for event in AddList[::-1]:
            # print("Adding AcceptEvent {} - {} at {}".format(date,event,insert_index))
            AddedDateAcceptEvents[year].insert(insert_index, event)
    return AddedDateAcceptEvents


def AddInQueueEventByDateFromFile(date, AddList, InQueueEvents):
    # print("InQueuEvents in func AddInQueueEventByDateFromFile {}".format(InQueueEvents))
    if not InQueueEvents:
        InQueueEvents = {}
    if parser.parse(date).year not in InQueueEvents.keys():
        InQueueEvents[parser.parse(date).year] = []
    ######Need to deep copy the list ######
    AddedDateInQueueEvents = copy.deepcopy(InQueueEvents)
    insert_index = len(InQueueEvents[parser.parse(date).year])

    # print("initialize insert_index {}".format(len(InQueueEvents[parser.parse(date).year])))
    for year, events in InQueueEvents.items():
        for index, event in enumerate(events[::-1]):
            caseno, severity, queue, casetime = event.split('-~')
            # print("Comparing {} {} {} {} to {} ".format(year,index,event,casetime,date))
            if parser.parse(casetime).date() < parser.parse(date).date():
                # print("Found Insert Inde-1 {}".format(index))
                insert_index = index
                break
        insert_index = len(AddedDateInQueueEvents[year]) - insert_index
        # print("Found Insert Index-2 {}".format(insert_index))
        for event in AddList[::-1]:
            AddedDateInQueueEvents[year].insert(insert_index, event)
    return AddedDateInQueueEvents


def CaseAcceptInOrderByTime(AllEventsList, date='2020-02-27', debug=False):
    shift_hour, gmt_hour = GetShiftHour(date)

    # 1 Case No #2 Severity #3 CaseAccept Type Case|FTS|UC #4 ccoid #5 Workgroup #6 Time
    Accept_Reg = re.compile(
        r'.*?MQToRedis:(\d{9})\s(\d)\s(Case|FTS|UC)_Accepted.*\sby\s(\w+)\s(.*)\s{0,1}at\s(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})')
    UC_Closed_Reg = re.compile(
        r'.*?MQToRedis:(\d{9})\s(\d)\sUC_Closed.*\sby\s(\w+)\s(.*)\s{0,1}at\s(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})')

    New_AllEventsList = []
    for event in AllEventsList:
        if 'Exception' not in event:
            New_AllEventsList.append(event)

    CaseRawAcceptList = []
    RawUCClosedList = []

    for line in AllEventsList:
        if re.search(r'_Accepted', line):
            result = re.search(Accept_Reg, line)
            casetype = result.group(3).strip()
            workgroup = result.group(5).strip()
            if not workgroup:
                workgroup = "Unknown"
            if casetype == 'FTS':
                workgroup = 'FTS_WORKGROUP'
            elif casetype == 'UC':
                workgroup = 'UC_WORKGROUP'
            # print("Parsing Accept Case Result: {} {} {}".format(line,casetype,workgroup))
            CaseRawAcceptList.append(result.group(1) + "-~" + result.group(2) + "-~" + result.group(4) + "-~" +
                                     workgroup + "-~" + result.group(6))
        elif re.search(r'UC_Closed', line):
            result = re.search(UC_Closed_Reg, line)
            RawUCClosedList.append(result.group(1) + "-~" + result.group(2) + "-~" + result.group(3) + "-~" +
                                   result.group(4) + "-~" + result.group(5))

    # CaseRawAcceptList = [re.search(Accept_Reg,line).group(1)+"-~"+
    #                     re.search(Accept_Reg,line).group(2)+"-~"+
    #                     re.search(Accept_Reg,line).group(4)+"-~"+
    #                     re.search(Accept_Reg,line).group(5)+"-~"+
    #                     re.search(Accept_Reg,line).group(6)
    #                     for line in New_AllEventsList if re.search(r'_Accepted',line)]

    # print("CaseRawAcceptList {}".format(CaseRawAcceptList))
    # print("CasAcceptInOrderByTime:Raw Accept List Length {} UC_Closed_List {}".format(len(CaseRawAcceptList),len(RawUCClosedList)))

    ###### Handling Accept Case ######
    DuplicateAcceptIndexList = []
    for index1, raw_case_line1 in enumerate(CaseRawAcceptList):
        caseno1, severity1, queue1, workgroup, time1 = raw_case_line1.split("-~")
        for index2, raw_case_line2 in enumerate(CaseRawAcceptList[index1 + 1:]):
            caseno2, severity2, queue2, workgroup, time2 = raw_case_line2.split("-~")
            if debug:
                pass
                # print("CasAcceptInOrderByTime:Comparing {} {} {} - {} {} {}".format(caseno1,queue1,time1,caseno2,queue2,time2))
            if caseno1 == caseno2 and time1 == time2:
                if debug:
                    print("Found dupliate {} {}".format(index1, index1 + index2 + 1))
                DuplicateAcceptIndexList.append(index1 + index2 + 1)
    DuplicateAcceptIndexList = sorted(list(set(DuplicateAcceptIndexList)))
    # print("CasAcceptInOrderByTime:Duplicate Case Index list {} {}".format(len(DuplicateAcceptIndexList),DuplicateAcceptIndexList))
    CaseAcceptRemoveDupExtList = [line for line in CaseRawAcceptList]
    for index in DuplicateAcceptIndexList[::-1]:
        # print("CasAcceptInOrderByTime:Pop duplicate {} from list".format(index))
        CaseAcceptRemoveDupExtList.pop(index)
        # print("CasAcceptInOrderByTime:After removing DuplicateCase length {}".format(len(CaseAcceptRemoveDupExtList)))

    # print("CaseAcceptRemoveDupExtList {}".format(CaseAcceptRemoveDupExtList))

    ###### Remove the case Accept time out of the current date ######
    CaseAcceptRemoveDupExtListWithDate = []
    for caseline in CaseAcceptRemoveDupExtList:
        # print(caseline)
        caseno, severity, ccoid, workgroup, casetime = caseline.split("-~")
        line_datetime = parser.parse(casetime)
        if line_datetime.strftime("%Y-%m-%d") == date:
            CaseAcceptRemoveDupExtListWithDate.append(caseline)

    # print("CaseAcceptRemoveDupExtListWithDate {}".format(CaseAcceptRemoveDupExtListWithDate))

    UniqueAcceptEventInOrderList = []
    for line in CaseAcceptRemoveDupExtListWithDate[::-1]:
        caseno, severity, ccoid, workgroup, timestamp = line.split('-~')
        isFoundDupCase = False
        for uniline in UniqueAcceptEventInOrderList[::-1]:
            unicaseno, severity, uniccoid, workgroup, unitimestamp = uniline.split('-~')
            if (unicaseno == caseno) and (uniccoid == ccoid):
                isFoundDupCase = True
                break
        if not isFoundDupCase:
            UniqueAcceptEventInOrderList.append(line)
            # print("UniqueAcceptEventInOrderList {}".format(UniqueAcceptEventInOrderList))

    ##### Handling UC_Closed Case ######
    DuplicateUCClosedIndexList = []
    for index1, raw_case_line1 in enumerate(RawUCClosedList):
        caseno1, severity1, ccoid1, workgroup1, time1 = raw_case_line1.split("-~")
        for index2, raw_case_line2 in enumerate(RawUCClosedList[index1 + 1:]):
            caseno2, severity2, ccoid2, workgroup2, time2 = raw_case_line2.split("-~")
            # print("CasAcceptInOrderByTime:Comparing {} {} {} - {} {} {}".format(caseno1,queue1,time1,caseno2,queue2,time2))
            if caseno1 == caseno2 and time1 == time2:
                # print("Found dupliate {} {}".format(index1,index1+index2+1))
                # DuplicateUCClosedIndexList.append(index1+index2+1)
                DuplicateUCClosedIndexList.append(index1)
    DuplicateUCClosedIndexList = sorted(list(set(DuplicateUCClosedIndexList)))
    # print("CaseUC_Cosed:Duplicate Closed Index list {} {}".format(len(DuplicateUCClosedIndexList),DuplicateUCClosedIndexList))

    CaseUCCLosedRemoveDupExtList = [line for line in RawUCClosedList]
    for index in DuplicateUCClosedIndexList[::-1]:
        # print("CasAcceptInOrderByTime:Pop duplicate {} from list".format(index))
        CaseUCCLosedRemoveDupExtList.pop(index)
        # print("CasAcceptInOrderByTime:After removing DuplicateCase length {}".format(len(CaseAcceptRemoveDupExtList)))

    ###### Remove the case UC_Closed time out of the current date ######
    CaseUCClosedRemoveDupExtListWithDate = []
    for caseline in CaseUCCLosedRemoveDupExtList:
        caseno, severity, ccoid, workgroup, casetime = caseline.split("-~")
        line_datetime = parser.parse(casetime)
        if line_datetime.strftime("%Y-%m-%d") == date:
            CaseUCClosedRemoveDupExtListWithDate.append(caseline)

    ###### From UniqueAcceptEventInOrderList remove UC_Closed by CaseUCClosedRemoveDupExtListWithDate ######
    ###### 2020-06-15 UC_Closed shoud not affect Case_Accepted bug for cas689283906 ######
    '''
    Found UC_Closed 5 689283906-~3-~knagavol-~UC_WORKGROUP -~2020-06-14 10:35:50 -- Accept 16 689283906-~3-~knagavol-~GCE-ACI-Solutions-~2020-06-14 06:34:24
    Found UC_Closed 2 689284486-~2-~prpratee-~UC_WORKGROUP -~2020-06-14 09:48:08 -- Accept 21 689284486-~2-~prpratee-~UC_WORKGROUP-~2020-06-14 06:05:16
    '''
    CaseAcceptRemoveUCClosedList = []
    CaseAcceptRemoveUCClosedIndexList = []
    for idx1, line1 in enumerate(UniqueAcceptEventInOrderList):
        caseno1, casesev1, ccoid1, workgroup1, timestamp1 = line1.split("-~")
        for idx2, line2 in enumerate(CaseUCCLosedRemoveDupExtList):
            caseno2, casesev2, ccoid2, workgroup2, timestamp2 = line2.split("-~")
            # if caseno1==caseno2 and ccoid1==ccoid2:
            #### adding workgroup comparasion
            if caseno1 == caseno2 and ccoid1 == ccoid2 and workgroup1 == workgroup2:
                print("Found UC_Closed {} {} -- Accept {} {}".format(idx2, line2, idx1, line1))
                CaseAcceptRemoveUCClosedIndexList.append(idx1)
    CaseAcceptRemoveUCClosedList = [line for idx, line in enumerate(UniqueAcceptEventInOrderList) if
                                    idx not in CaseAcceptRemoveUCClosedIndexList]
    # print("CaseAcceptRemoveUCClosedList {}".format(CaseAcceptRemoveUCClosedList))

    return CaseAcceptRemoveUCClosedList[::-1]


def CaseTakenByEngrGrpByDate(start_date='2020-06-17', end_date=datetime.datetime.today().strftime("%Y-%m-%d"),
                             RawAcceptEventsByDate={}):
    CaseTakenByEngrByDate = {}  # {'2020-50-23':{'APT-ACI-SOLUTIONS':{'siddhp':[689146430,689148487]}}}
    for date, items in RawAcceptEventsByDate.items():

        if parser.parse(date) < parser.parse(start_date):
            continue
        elif parser.parse(date) > parser.parse(end_date):
            break

        # print("Processing date {}".format(date))
        if date not in CaseTakenByEngrByDate.keys():
            CaseTakenByEngrByDate[date] = {}
        for caseno, casetakerlist in items.items():
            # print("Case {} - List {}".format(caseno,casetakerlist))
            for casetaker in casetakerlist:
                # print("Case {} - List {} Taker {}".format(caseno,casetakerlist,casetaker))
                if casetaker[1] not in CaseTakenByEngrByDate[date].keys():
                    CaseTakenByEngrByDate[date][casetaker[1]] = {}
                if casetaker[0] not in CaseTakenByEngrByDate[date][casetaker[1]].keys():
                    CaseTakenByEngrByDate[date][casetaker[1]][casetaker[0]] = []
                # print("Adding {} in {} {}".format(caseno,casetaker[1],casetaker[0]))
                CaseTakenByEngrByDate[date][casetaker[1]][casetaker[0]].append(caseno)

        # print(CaseTakenByEngrByDate['2020-06-24']['APT-SV'])
        Tmp_CaseTakenByEngrByDate = copy.deepcopy(CaseTakenByEngrByDate)

        ##### Move FTS_WORKGROUP an UC_WORKGRUOP case to InterestWorkgroup Case ######
        for casetype, takenlist in CaseTakenByEngrByDate[date].items():
            if casetype != 'UC_WORKGROUP' and casetype != 'FTS_WORKGROUP':
                continue
            # print("UC/FTS {} {} {}".format(date,casetype,takenlist))
            for ccoid, caselist in CaseTakenByEngrByDate[date][casetype].items():
                ccoid, new_wg, find_date = FindEngrWorkgroup(date, ccoid, RawAcceptEventsByDate)
                new_wg = new_wg.strip()
                if new_wg != "Unknown":
                    # print("ccoid {} in {} find new_wg: {} on {}".format(ccoid,casetype,new_wg,find_date))
                    if new_wg not in Tmp_CaseTakenByEngrByDate[date].keys():
                        # print("Adding new WG {}".format(new_wg))
                        Tmp_CaseTakenByEngrByDate[date][new_wg] = {}
                    if ccoid not in Tmp_CaseTakenByEngrByDate[date][new_wg].keys():
                        # print("Adding new WG {} new ccoid {}".format(new_wg,ccoid))
                        # print("Current -- {}".format(Tmp_CaseTakenByEngrByDate))
                        Tmp_CaseTakenByEngrByDate[date][new_wg][ccoid] = []
                    Tmp_CaseTakenByEngrByDate[date][new_wg][ccoid] = Tmp_CaseTakenByEngrByDate[date][new_wg][
                                                                         ccoid] + caselist
            # print(Tmp_CaseTakenByEngrByDate['2020-06-28'])
            CaseTakenByEngrByDate = copy.deepcopy(Tmp_CaseTakenByEngrByDate)

            # ccoid,new_wg,date = FindEngrWorkgroup(date,engr[0],RawAcceptEventsByDate)
    return CaseTakenByEngrByDate


def ConvertAcceptEventsByDate(start_date='2020-02-27', end_date=datetime.datetime.today().strftime("%Y-%m-%d"),
                              AcceptEventsFromFile=[]):
    '''
    Input: 2020_AcceptEvent.txt
    No Shift check is needed as the AcceptEvent are from APJC shift
    Output:
    {'689241333': [['yiding2', 'JAPAN-ACI']],
         '689246419': [['junwa', 'UC_WORKGROUP']],
         '689247993': [['raghb', 'APT-ACI-SOLUTIONS2']],
         '689248026': [['reperuma', 'APT-ACI-SOLUTIONS2']],
         '689242958': [['tskanai', 'JAPAN-ACI']],
         '688563612': [['tonzeng', 'APT-ACI-SOLUTIONS']],
         '689248175': [['juoishi', 'JAPAN-HTTS-FLETS']],
         '689248248': [['junwa', 'APT-ACI-SOLUTIONS']],
         '689248290': [['koiwata', 'JAPAN-NEXUS']],
         '689248319': [['siddhp', 'APT-ACI-SOLUTIONS']],
         '689211356': [['shubhada', 'UC_WORKGROUP']],
         '689230467': [['yuxuliu', 'UC_WORKGROUP']],
         '689248577': [['yuxuliu', 'APT-GC-Solution']],
         '689248444': [['ykamimur', 'JAPAN-ACI']],
         '689247673': [['gauvasud', 'APT-ACI-SOLUTIONS2']],
         '689248613': [['jawalia', 'APT-ACI-SOLUTIONS2'],
          ['huaizhao', 'APT-GC-Solution']],
         '689206025': [['jawalia', 'APT-ACI-SOLUTIONS2']],
         '689248692': [['fushuang', 'APT-GC-Solution']],
         '689241901': [['maveer', 'APT-ACI-SOLUTIONS2']],
         '689190081': [['deepaky', 'APT-ACI-SOLUTIONS2']],
         '689248680': [['ttaoda', 'JAPAN-HTTS-FLETS']],
         '689220318': [['dawang', 'APT-GC-Solution']],
         '689076996': [['hethakur', 'APT-ACI-SOLUTIONS2']],
         '689248849': [['pli3', 'APT-GC-Solution']],
         '689248974': [['mkamijo', 'JAPAN-ACI']],
         '689248966': [['amikum', 'GCE-ACI-Solutions']],
         '689249029': [['yushimaz', 'JAPAN-ACI']],
         '689171782': [['krajasel', 'UC_WORKGROUP']],
         '689249154': [['tonzeng', 'APT-ACI-SOLUTIONS']],
         '689154452': [['amikum', 'GCE-ACI-Solutions']]}
    '''
    AcceptEventsByDate = {}
    AcceptCaseSevByDate = {}

    for year, events in AcceptEventsFromFile.items():
        if year < parser.parse(start_date).year:
            continue
        elif year > parser.parse(end_date).year:
            break
        for event in events:
            caseno, casesev, ccoid, workgroup, timestamp = event.split('-~')
            if parser.parse(timestamp) < parser.parse(start_date):
                continue
            elif parser.parse(timestamp) > parser.parse(end_date) + datetime.timedelta(days=1):
                break
            date = parser.parse(timestamp).strftime("%Y-%m-%d")
            if date not in AcceptEventsByDate.keys():
                AcceptEventsByDate[date] = {}
                AcceptCaseSevByDate[date] = {}
                AcceptCaseSevByDate[date]['1'] = []
                AcceptCaseSevByDate[date]['2'] = []
                AcceptCaseSevByDate[date]['3'] = []
                AcceptCaseSevByDate[date]['4'] = []

            if caseno not in AcceptEventsByDate[date].keys():
                AcceptEventsByDate[date][caseno] = []
            if ccoid != 'lowtouch':
                AcceptEventsByDate[date][caseno].append([ccoid, workgroup])
                AcceptCaseSevByDate[date][casesev].append(caseno)

    return AcceptEventsByDate, AcceptCaseSevByDate


def ConvertInQueueEventsByDate(start_date='2020-02-27', end_date=datetime.datetime.today().strftime("%Y-%m-%d"),
                               InQueueEventsFromFile={}):
    '''
    Input : 2020_InQueueEvent.txt
    No Shift check needed as the InQueue event are from APJC shift period
    {'All': ['689154452-~1-~FTS-~2020-06-09 00:02:18',
      '689248026-~3-~CX-APJC-BLR-ACI-SSPT-~2020-06-09 00:14:11',
      '689247673-~3-~FTS-~2020-06-09 00:28:44',
      '688563612-~1-~FTS-~2020-06-09 00:59:46',
      '689248319-~3-~CX-APJC-SYD-ACI-SSPT-~2020-06-09 01:45:19',
      '689211356-~3-~UC-~2020-06-09 02:16:22',
      '689248637-~3-~CX-APJC-BLR-ACI-SSPT-~2020-06-09 03:05:42',
      '689206025-~2-~CX-APJC-BLR-ACI-SSPT-~2020-06-09 03:18:10',
      '689241901-~3-~CX-APJC-BLR-ACI-SSPT-~2020-06-09 03:30:13',
      '689237505-~3-~UC-~2020-06-09 03:44:42',
      '689190081-~3-~CX-APJC-BLR-ACI-SSPT-~2020-06-09 03:50:47',
      '689248857-~3-~CX-APJC-SYD-ACI-SSPT-~2020-06-09 04:05:49',
      '689076996-~3-~CX-APJC-BLR-ACI-SSPT-~2020-06-09 04:08:11',
      '689248966-~3-~CX-APJC-BLR-ACI-SSPT-~2020-06-09 04:46:13',
      '689249154-~3-~CX-APJC-SYD-ACI-SSPT-~2020-06-09 05:38:24'],
     'FTS': ['689154452', '689247673', '688563612'],
     'CX-APJC-BLR-ACI-SSPT': ['689248026',
      '689248637',
      '689206025',
      '689241901',
      '689190081',
      '689076996',
      '689248966'],
     'CX-APJC-SYD-ACI-SSPT': ['689248319', '689248857', '689249154'],
     'UC': ['689211356', '689237505']}
     '''
    InQueueEventsByDate = {}  # {'2020-05-22,{'CX-APJC-BLR-ACI-SSPT':[689148383],'CX-APJC-SYD-ACI-SSPT':[689148487]}}

    for year, events in InQueueEventsFromFile.items():
        if year < parser.parse(start_date).year:
            continue
        elif year > parser.parse(end_date).year:
            break
        for event in events:
            caseno, casesev, queue, timestamp = event.split('-~')
            # print(" {} - {}".format(timestamp,end_date))
            if parser.parse(timestamp) < parser.parse(start_date):
                continue
            elif parser.parse(timestamp) >= parser.parse(end_date) + datetime.timedelta(days=1):
                break
            date = parser.parse(timestamp).strftime("%Y-%m-%d")
            if date not in InQueueEventsByDate.keys():
                InQueueEventsByDate[date] = {}
                InQueueEventsByDate[date]['All'] = []
                InQueueEventsByDate[date]['AllCases'] = []

            if queue not in InQueueEventsByDate[date]:
                InQueueEventsByDate[date][queue] = []
            InQueueEventsByDate[date][queue].append(caseno)
            InQueueEventsByDate[date]['All'].append(event)
            InQueueEventsByDate[date]['AllCases'].append(caseno)

    return InQueueEventsByDate


def FindEngrWorkgroup(date, ccoid, AcceptEventsByDate):
    end_datetime = parser.parse('2020-02-27')
    cur_datetime = parser.parse(date)
    while cur_datetime > end_datetime:
        cur_date = cur_datetime.strftime("%Y-%m-%d")
        if cur_date in AcceptEventsByDate.keys():
            for caseno, caestakerlist in AcceptEventsByDate[cur_date].items():
                for casetaker in caestakerlist:
                    if ccoid == casetaker[0] and casetaker[1] != 'UC_WORKGROUP' and casetaker[1] != 'FTS_WORKGROUP':
                        # print("Found {} in workgroup {} on date {} from case {}".format(ccoid,casetaker[1],cur_date,caseno))
                        return ccoid, casetaker[1], cur_date
        cur_datetime = cur_datetime + datetime.timedelta(days=-1)
    return ccoid, "Unknown", date


def FindAcceptEventsFromEventFile(acceptfilelist):
    if len(acceptfilelist) == 0:
        return
    AcceptEvents_by_year = {}
    ###### Accept file parsing Read the current Parsing file 2020_InQueue.txt ######
    for acceptfile in acceptfilelist:
        with open(acceptfile, 'r') as f:
            ReadAcceptEvents = f.readlines()
        f.close()
        ReadAcceptEvents = [event.strip() for event in ReadAcceptEvents if event.strip()]
        for event in ReadAcceptEvents:
            caseno, casesev, ccoid, workgroup, timestamp = event.split("-~")
            caseyear = parser.parse(timestamp).year
            if caseyear not in AcceptEvents_by_year.keys():
                AcceptEvents_by_year[caseyear] = []
            AcceptEvents_by_year[caseyear].append(event)
    return AcceptEvents_by_year


def FindInQueueEventsFromEventFile(inqueuefilelist):
    if len(inqueuefilelist) == 0:
        return "1970-01-01", {}
    InQueueEvents_by_year = {}

    import os
    # shift_hour,gmt_hour = ACILib.GetShiftHour(date)

    for inqueuefile in inqueuefilelist:

        ###### Source file only for the timestamps the tracking report is genreate at ######
        sourcefiletime = os.path.getmtime(inqueuefile)
        sourcefiledatetime = datetime.datetime.fromtimestamp(
            sourcefiletime)  # + datetime.timedelta(hours=(gmt_hour+shift_hour[0]))
        sourcefileformattime = sourcefiledatetime.strftime("%Y-%m-%d %H:%M:%S")

        with open(inqueuefile, 'r') as f:
            ReadInQueueEvents = f.readlines()
        f.close()
        ReadInQueueEvents = [event.strip() for event in ReadInQueueEvents if event.strip()]
        for event in ReadInQueueEvents:
            caseno, casesev, queue, timestamp = event.split("-~")
            caseyear = parser.parse(timestamp).year
            if caseyear not in InQueueEvents_by_year.keys():
                InQueueEvents_by_year[caseyear] = []
            InQueueEvents_by_year[caseyear].append(event)

    return sourcefileformattime, InQueueEvents_by_year


def FindInQueueEvent(CaseEventsList, InterestQueueName=[], shift_start_hour=0, shift_end_hour=6, debug=False):
    InterestQueueName = InterestQueueName

    # 1 Case Number #2 Case Priority #3 Case Qeueue #4 Event Timestamp
    InQueue_Reg = re.compile(
        r'.*?MQToRedis:(\d{9})\s(\d).*Case_InQueue\s(.+?)\s.*at\s(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})')
    # 1 Case Number #2 Case Priority #3 Event Timestamp
    FTS_Reg = re.compile(r'.*?MQToRedis:(\d{9})\s(\d).*FTS_InQueue\s.*at\s(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})')
    UC_Reg = re.compile(r'.*?MQToRedis:(\d{9})\s(\d).*UC_InQueue.*at\s(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})')

    CaseInQueueRawList = []
    FTSInQueueRawList = []
    UCInQueueRawList = []

    for line in CaseEventsList:
        if 'Case_InQueue' in line:
            # print(line)
            # break
            if re.search(InQueue_Reg, line):
                CaseInQueueRawList.append(re.search(InQueue_Reg, line).group(1) + "-~" +
                                          re.search(InQueue_Reg, line).group(2) + "-~" +
                                          re.search(InQueue_Reg, line).group(3) + "-~" +
                                          re.search(InQueue_Reg, line).group(4))

    # CaseInQueueRawList = [re.search(InQueue_Reg,line).group(1)+"-~"+
    #                      re.search(InQueue_Reg,line).group(2)+"-~"+
    #                      re.search(InQueue_Reg,line).group(3)+"-~"+
    #                      re.search(InQueue_Reg,line).group(4) 
    #                      for line in CaseEventsList if 'Case_InQueue' in line]

    for line in CaseEventsList:
        if 'FTS_InQueue' in line:
            # print(line)
            if re.search(FTS_Reg, line):
                # print("Add FTS ".format(line))
                FTSInQueueRawList.append(re.search(FTS_Reg, line).group(1) + "-~" +
                                         re.search(FTS_Reg, line).group(2) + "-~FTS-~" +
                                         re.search(FTS_Reg, line).group(3))

    # FTSInQueueRawList = [re.search(FTS_Reg,line).group(1)+"-~"+
    #                     re.search(FTS_Reg,line).group(2)+"-~FTS-~"+
    #                     re.search(FTS_Reg,line).group(3) 
    #                     for line in CaseEventsList if 'FTS_InQueue' in line]

    UCInQueueRawList = [re.search(UC_Reg, line).group(1) + "-~" +
                        re.search(UC_Reg, line).group(2) + "-~UC-~" +
                        re.search(UC_Reg, line).group(3)
                        for line in CaseEventsList if 'UC_InQueue' in line]

    ###### if the case case in before shift start and event in the shift start, it will still be recorded, need to remove ######
    # 2020-03-06 01:00:19,511-INFO-MQToRedis:688593987 3 Case_InQueue WW-ACI-Solutions L2NodeAuthPolicy at 2020-03-06 00:58:47
    # Example is as above
    CaseInQueueRawRemoveBeforeShiftEventList = []
    for caseline in CaseInQueueRawList:
        # print(caseline)
        caseno, priority, queue, casetime = caseline.split("-~")
        case_datetime = parser.parse(casetime)
        if case_datetime.hour >= shift_start_hour and case_datetime.hour < shift_end_hour:
            CaseInQueueRawRemoveBeforeShiftEventList.append(caseline)
    CaseInQueueRawList = CaseInQueueRawRemoveBeforeShiftEventList

    if debug:
        print("Original CaseInQueue List length {}".format(len(CaseInQueueRawList)))
        print("Original FTSInQueue List length {}".format(len(FTSInQueueRawList)))
        print("Original UCInQueue List length {}".format(len(UCInQueueRawList)))

    NotInterestQueueIndexList = [index for index, case in enumerate(CaseInQueueRawList) if
                                 case.split("-~")[2] not in InterestQueueName]

    if debug:
        print("Not Interest Queue Index list {}".format(NotInterestQueueIndexList))

    CaseInQueueRemoveNotInterestQueueExtList = [line for line in CaseInQueueRawList]

    for index in NotInterestQueueIndexList[::-1]:
        # print("Pop not interest {} from list".format(index))
        CaseInQueueRemoveNotInterestQueueExtList.pop(index)

    CaseInQueueRemoveNotInterestQueueExtList = list(set(CaseInQueueRemoveNotInterestQueueExtList))

    if debug:
        print("After removing NotInterestQueue length {}".format(len(CaseInQueueRemoveNotInterestQueueExtList)))
        # for case in CaseInQueueRemoveNotInterestQueueExtList:
        #    print(case)

    DuplicateInQueueIndexList = []
    for index1, raw_case_line1 in enumerate(CaseInQueueRemoveNotInterestQueueExtList):
        caseno1, priority1, queue1, time1 = raw_case_line1.split("-~")
        for index2, raw_case_line2 in enumerate(CaseInQueueRemoveNotInterestQueueExtList[index1 + 1:]):
            caseno2, priority2, queue2, time2 = raw_case_line2.split("-~")
            # print("Comparing {} {} {} - {} {} {}".format(caseno1,queue1,time1,caseno2,queue2,time2))
            if caseno1 == caseno2 and time1 == time2:
                # print("Found dupliate {} {}".format(index1,index1+index2+1))
                DuplicateInQueueIndexList.append(index1 + index2 + 1)
    if debug:
        print("Duplicate Case Index list {}".format(DuplicateInQueueIndexList))
        for case in DuplicateInQueueIndexList:
            print(case)

    CaseInQueueRemoveDupExtList = [line for line in CaseInQueueRemoveNotInterestQueueExtList]
    for index in DuplicateInQueueIndexList[::-1]:
        # print("Pop duplicate {} from list".format(index))
        CaseInQueueRemoveDupExtList.pop(index)
    if debug:
        print("After removing DuplicateCase length {}".format(len(CaseInQueueRemoveDupExtList)))

    return CaseInQueueRemoveDupExtList + FTSInQueueRawList + UCInQueueRawList


def FindDispatchEvent(CaseEventsList, shift='apjc', debug=False):
    RawDispatchedEventList = []

    # Group 1.	2932-2941	689101876
    # Group 2.	2942-2943	3
    # Group 3.	2964-3033	APIC Appliance || Maintenance window / Standby (Closed Wednesday 19)
    # Group 4.	3037-3056	2020-05-17 01:00:00
    # Group 5.	3060-3066	+05:30
    # Group 6.	3067-3102	 India Standard Time (Asia/Kolkata)
    Dispatch_Reg = re.compile(
        r'.*?MQToRedis:(\d{9})\s(\d).*Case_Dispatched_Out\s(.+?)To\s\s(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\(GMT([+-]\d{2}:\d{2})\)(.+)')

    for line in CaseEventsList:
        if 'Case_Dispatched_Out' in line:
            dispatch_line = re.search(Dispatch_Reg, line)
            if dispatch_line:
                caseno = dispatch_line.group(1)
                severity = dispatch_line.group(2)
                casetitle = dispatch_line.group(3).strip()
                timestamp = dispatch_line.group(4)
                # Two type of the timezone
                # 2020-02-09 00:30:00(GMT+03:00) Europe/Istanbul
                # 2020-01-08 08:30:00(GMT-06:00) Central Standard Time (America/Chicago)
                if re.search(r'.+?\((.+)\)', dispatch_line.group(6)):
                    timezone = re.search(r'.+?\((.+)\)', dispatch_line.group(6)).group(1)
                else:
                    timezone = dispatch_line.group(6)
                ###### The return value of the isOnShift is apjc based on AESTorAEDT, emea based on IST ######
                ShiftInd, timestamp_offset = isOnShift(timestamp, timezone, shift=shift, before_shift_hours_offset=1)
                if ShiftInd == "On":
                    # print("OnShift {} {} {} {}".format(caseno,timestamp,timezone,line))
                    RawDispatchedEventList.append("-~".join([caseno, severity, timestamp_offset, casetitle]))

    ###### Remove multiple dispatched and keep only the last one ######
    RemoveDuplicateDispatchedEventIdx = []
    RemoveDuplicateDispatchedEventList = []
    ExistingDispatchCaseDic = {}  # {'Date':[CaseNoList]}

    for idx, line in enumerate(RawDispatchedEventList[::-1]):
        caseno, casesev, casetime, casetitle = line.split('-~')
        date = parser.parse(casetime).strftime("%Y-%m-%d")
        if date not in ExistingDispatchCaseDic.keys():
            ExistingDispatchCaseDic[date] = []
        if caseno not in ExistingDispatchCaseDic[date]:
            ExistingDispatchCaseDic[date].append(caseno)
        else:
            RemoveDuplicateDispatchedEventIdx.append(len(RawDispatchedEventList) - idx - 1)

    # print(set(RemoveDuplicateDispatchedEventIdx))
    for idx, line in enumerate(RawDispatchedEventList):
        if idx not in set(RemoveDuplicateDispatchedEventIdx):
            RemoveDuplicateDispatchedEventList.append(line)

    ###### Sort the Dispatched Case ######
    DispatchedEventRemainingIdx = [i for i in range(len(RemoveDuplicateDispatchedEventList))]
    SortedDispatchedEventIdx = []

    for idx in range(len(RemoveDuplicateDispatchedEventList)):
        smallest_idx = DispatchedEventRemainingIdx[0]
        caseno, casesev, smallest_time, casetitle = RemoveDuplicateDispatchedEventList[smallest_idx].split('-~')
        # print("Round {} Setting Smallest {}".format(smallest_idx,casetime1))
        for idx2, line2 in enumerate(RemoveDuplicateDispatchedEventList):
            if idx2 in SortedDispatchedEventIdx:
                continue
            caseno2, casesev2, casetime2, casetitle2 = line2.split('-~')
            if parser.parse(casetime2) < parser.parse(smallest_time):
                # print("Found Smallest {} {}".format(idx2,casetime2))
                smallest_idx = idx2
                smallest_time = casetime2
                # print("Round {} Smallext_idx {}".format(idx,smallest_idx))
        DispatchedEventRemainingIdx.remove(smallest_idx)
        SortedDispatchedEventIdx.append(smallest_idx)

    SortedDispatchedEventList = []
    for idx in SortedDispatchedEventIdx:
        SortedDispatchedEventList.append(RemoveDuplicateDispatchedEventList[idx])

    return SortedDispatchedEventList


def GetStatsFromCaseAcceptInOrderByTime(AcceptEventInOrderList, CaseStatsDic, EngrList):
    SYDEngrList = EngrList[0]
    SYDOtherEngrList = EngrList[1]
    BGLEngrList = EngrList[2]
    BGLOtherEngrList = EngrList[3]

    SydOnShiftEngrList = []
    SydOtherOnshiftEngrList = []

    BGLOnShiftEngrList = []
    BGLOtherOnshiftEngrList = []

    ###### Getting partial CaseStatsDic Stats from the orderred List ######
    for caseline in AcceptEventInOrderList:
        caseno, severity, ccoid, workgroup, time = caseline.split("-~")
        if ccoid in SYDEngrList:
            if ccoid not in SydOnShiftEngrList:
                SydOnShiftEngrList.append(ccoid)
        elif ccoid in SYDOtherEngrList:
            if ccoid not in SydOtherOnshiftEngrList:
                SydOtherOnshiftEngrList.append(ccoid)
        elif ccoid in BGLEngrList:
            if ccoid not in BGLOnShiftEngrList:
                BGLOnShiftEngrList.append(ccoid)
        elif ccoid in BGLOtherEngrList:
            if ccoid not in BGLOtherOnshiftEngrList:
                BGLOtherOnshiftEngrList.append(ccoid)
    CaseStatsDic['SydOnShiftEngr'] = SydOnShiftEngrList
    CaseStatsDic['BGLOnShiftEngr'] = BGLOnShiftEngrList
    CaseStatsDic['SYDHelper'] = SydOtherOnshiftEngrList
    CaseStatsDic['BGLHelper'] = BGLOtherOnshiftEngrList

    return CaseStatsDic


def GetStatsFromInQueueEventInOrderList(InQueueEventInOrderList, CaseStatsDic):
    ###### Getting partial CaseStatsDic Stats from the orderred List ######
    for caseline in InQueueEventInOrderList:
        caseno, priority, queue, time = caseline.split("-~")
        if 'SYD' in queue:
            CaseStatsDic['SydQueueVol'] = CaseStatsDic['SydQueueVol'] + 1
            CaseStatsDic['SydQueueVolByPri'][int(priority)] = CaseStatsDic['SydQueueVolByPri'][int(priority)] + 1
        elif 'BLR' in queue:
            CaseStatsDic['BGLQueueVol'] = CaseStatsDic['BGLQueueVol'] + 1
            CaseStatsDic['BGLQueueVolByPri'][int(priority)] = CaseStatsDic['BGLQueueVolByPri'][int(priority)] + 1
        elif 'FTS' in queue:
            CaseStatsDic['FTSCaseVol'] = CaseStatsDic['FTSCaseVol'] + 1
        elif 'UC' in queue:
            CaseStatsDic['UCCaseVol'] = CaseStatsDic['UCCaseVol'] + 1

    return CaseStatsDic


def GetShiftHour(date='2020-04-05', shift='apjc'):
    date_datetime = parser.parse(date)

    ShiftTime = {
        '2020Summer': ['2019-10-10', '2020-03-28'],
        '2020InterToWinter': ['2020-03-29', '2020-04-04'],
        '2020Winter': ['2020-04-05', '2020-10-03'],
        '2020InterToSummer': ['2020-10-04', '2020-10-03'],
        '2020InterToSummer2': ['2020-10-04', '2020-10-25'],
        '2020Summer': ['2020-10-26', '2021-03-27']
    }
    ShiftHour = {
        'Summer': [1, 7],
        'InterToWinter': [0, 6],
        'Winter': [0, 6],
        'InterToSummer': [0, 6],
        'InterToSummer2': [2, 8],
        'Summer': [1, 7]
    }

    AESTorAEDT = {
        '10': [
            ['2020-04-04', '2020-10-04'],
            ['2021-04-05', '2021-10-03']
        ],
        '11': [
            ['2019-10-27', '2020-04-04'],
            ['2020-10-04', '2021-04-04']
        ]
    }

    GMT_start = -1
    ShiftStartHour = []

    for key, period in ShiftTime.items():
        year, sfhit, start_datetime, end_datetime = key[:4], key[4:], parser.parse(period[0]), parser.parse(period[1])
        # print("GetShiftHour - {} v.s. {} {} {} {}".format(date, year,sfhit,period[0],period[1]))
        if date_datetime >= start_datetime and date_datetime <= end_datetime:
            ShiftStartHour = ShiftHour[key[4:]]  # [1, 7]
            break

    if shift == 'apjc':
        for gmthour, periodlist in AESTorAEDT.items():
            for period in periodlist:
                # print(period)
                if date_datetime >= parser.parse(period[0]) and date_datetime <= parser.parse(period[1]):
                    GMT_start = gmthour
                    break

    if shift == 'emea':
        GMT_start = 5.5
        ShiftStartHour[0] = ShiftStartHour[0] + 6
        ShiftStartHour[1] = ShiftStartHour[1] + 6

    # print("ShiftStartHourInGMT {} StartGMT {}".format(ShiftStartHour[0],GMT))
    return ShiftStartHour, float(GMT_start)


def isOnShift(timestamp, timezone='America/Los_Angeles', shift='apjc', before_shift_hours_offset=0,
              after_shift_hours_offset=0, debug=False):
    '''
    before_shift_hours_offset is the hours before shift if would like to be considered to be onshift, default is 0
    after_shift_hours_offset is the hours after shift if would like to be considered to be onshift, default is 0
    before_shift_hours_offset and after_shift_hours_offset is majorly used for dispatched case that dispatched one hour prior to shift would be considered.
    
    local = pytz.timezone ("America/Los_Angeles")
    naive = datetime.datetime.strptime ("2001-2-3 10:11:12", "%Y-%m-%d %H:%M:%S")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    India Standard Time (Asia/Kolkata)
    '''
    print("isOnShift {}".format(timestamp))
    date, time = timestamp.split()
    timezone = timezone.strip()

    local = pytz.timezone(timezone)
    local_dt = local.localize(parser.parse(timestamp))
    local_gmt_offset = local_dt.utcoffset().total_seconds() / 60 / 60
    utc_dt = local_dt.astimezone(pytz.utc)
    # print("InputTime:{} TimeZone:{} GMTOffset:{} UTCTime:{}".format(
    #    timestamp,timezone,local_gmt_offset,utc_dt.strftime("%Y-%m-%d %H:%M:%S")))
    utc_date = utc_dt.strftime("%Y-%m-%d")
    utc_time = utc_dt.strftime("%H:%M:%S")
    hour = utc_dt.hour
    minute = utc_dt.minute

    shift_hour, GMT_start = GetShiftHour(date, shift)
    orig_shift_hour = shift_hour.copy()
    ###### If offset is considered, plus 24 as event might be at 23:00 - 24:00 the day before ######
    if before_shift_hours_offset != 0 or after_shift_hours_offset != 0:
        shift_hour[0] = shift_hour[0] + 24 - before_shift_hours_offset
        shift_hour[1] = shift_hour[1] + after_shift_hours_offset + 24
        if hour <= 7:
            hour = hour + 24

    if debug:
        print("Case UTC {} {}".format(utc_date, utc_time))
        print("isOnShift:Shift Hour {} {} Start GMT {}".format(shift_hour, orig_shift_hour, GMT_start))
        print("isOnShift:Hour {} Minute {}".format(hour, minute))

    if hour >= shift_hour[0] and hour < shift_hour[1]:
        if debug:
            print("isOnShift:IsOnShift {}".format(utc_date + ' ' + utc_time))
        # return "On", (utc_dt + datetime.timedelta(hours=GMT_start+orig_shift_hour[0])).strftime("%Y-%m-%d %H:%M:%S")
        return "On", (utc_dt + datetime.timedelta(hours=GMT_start)).strftime("%Y-%m-%d %H:%M:%S")
    else:
        if debug:
            print("isOnShift:OffShift {}".format(utc_date + ' ' + utc_time))
        # return "Off", (utc_dt + datetime.timedelta(hours=(GMT_start+orig_shift_hour[0]))).strftime("%Y-%m-%d %H:%M:%S")
        return "Off", (utc_dt + datetime.timedelta(hours=(GMT_start))).strftime("%Y-%m-%d %H:%M:%S")


def GetRawEventsFromDate(allevents, date='2020-02-27', shift_start_hour=0, shift_end_hour=6, debug=False):
    date = date
    shift_start_hour = shift_start_hour
    shift_end_hour = shift_end_hour
    allevents_in_date = []

    CaseMatchLine_Reg = re.compile(r'.*?MQToRedis:\d{9}\s\d\s.*at\s(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})')
    Dispatch_Reg = re.compile(
        r'.*?MQToRedis:(\d{9})\s(\d).*Case_Dispatched_Out\s(.+?)To\s\s(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\(GMT([+-]\d{2}:\d{2})\)(.+)')
    for line in allevents[:]:
        if date not in line:
            continue
        if re.search(CaseMatchLine_Reg, line):
            line_datetime = parser.parse(re.search(CaseMatchLine_Reg, line).group(1))
            # dispatched case might dispatch to today while not take into account

            if line_datetime.strftime("%Y-%m-%d") != date:
                # print("{} - {}".format(line_datetime.strftime("%Y-%m-%d"),date))
                continue
            if line_datetime.hour >= shift_start_hour and line_datetime.hour < shift_end_hour:
                allevents_in_date.append(line)
    return allevents_in_date


def RemoveNotInQueueAcceptCase(start_date='2020-02-27', end_date=datetime.datetime.today().strftime("%Y-%m-%d"),
                               RawAcceptEventsByDate=[], InQueueEventsByDate=[],
                               InterestWorkgroup=['APT-ACI-SOLUTIONS', 'APT-ACI-SOLUTIONS2']):
    RemoveNotInQueueAcceptEventsByDate = copy.deepcopy(RawAcceptEventsByDate)
    for date, events in RawAcceptEventsByDate.items():
        if parser.parse(date) < parser.parse(start_date):
            continue
        elif parser.parse(date) > parser.parse(end_date):
            break
        InQueueCaseList = []
        RemoveCaseList = []
        for casetype, caselist in InQueueEventsByDate[date].items():
            InQueueCaseList = [*InQueueCaseList, *caselist]
        ###### Remove the case which is not in queue but taken and keep workgroup engineer yanked case by InterestWorkgroup######
        for caseno, casetakerlist in RawAcceptEventsByDate[date].items():
            # if date == '2020-05-24':
            #    print("{} {} {} {}".format(date,caseno,casetakerlist,InQueueCaseList))
            if caseno not in InQueueCaseList:
                ###### If there is a yank case which is not in queue, but yanked by APT-ACI-SOLUTIONS/2 engineer, it wont be removed ######.
                isYankedCase = False
                for casetaker in casetakerlist:
                    if casetaker[1] in InterestWorkgroup:
                        # print("{} {} is a yanked case, keep in the accepted list".format(date,caseno))
                        isYankedCase = True
                if not isYankedCase:
                    # print("{} Removing the case {} as it is not the InQueue case".format(date,caseno))
                    RemoveCaseList.append(caseno)
        # if date == '2020-05-24':
        # print("Remove Case List {}".format(RemoveCaseList))
        for caseno in RemoveCaseList:
            del RemoveNotInQueueAcceptEventsByDate[date][caseno]

    UpdWGAcceptEventsByDate = copy.deepcopy(RemoveNotInQueueAcceptEventsByDate)
    # print("After Remove Case List {}".format(UpdWGAcceptEventsByDate['2020-05-24']))
    ###### Check UC_WORKGROUP and FTS_WORKGROUP Put in the right workgroup #######
    for date, caselist in RemoveNotInQueueAcceptEventsByDate.items():
        if parser.parse(date) < parser.parse(start_date):
            continue
        elif parser.parse(date) > parser.parse(end_date):
            break
        for caseno, casetakerlist in caselist.items():
            for idx, casetaker in enumerate(casetakerlist):
                if casetaker[1] not in InterestWorkgroup:
                    # print("Finding Correct Workgroup for {}".format(casetaker[1]))
                    ccoid, workgroup, date_wg = FindEngrWorkgroup(date, casetaker[0], RawAcceptEventsByDate)
                    if workgroup != "Unknown":
                        # print("caseno {} {} {} {}".format(caseno,ccoid,workgroup,date_wg))
                        UpdWGAcceptEventsByDate[date][caseno][idx][1] = workgroup
    # print("Return Accept case list by date {}".format(UpdWGAcceptEventsByDate['2020-05-24']))
    return UpdWGAcceptEventsByDate


def RemoveAcceptEventByDateFromFile(date, AcceptEvents):
    if not AcceptEvents:
        return {}
    ######Need to deep copy the list ######
    RemovedDateAcceptEvents = copy.deepcopy(AcceptEvents)
    for year, events in AcceptEvents.items():
        for index, event in enumerate(AcceptEvents[year][::-1]):
            caseno, severity, ccoid, workgroup, casetime = event.split('-~')
            if parser.parse(casetime).strftime("%Y-%m-%d") == date:
                # print("Removing AcceptEvents {} - {} ".format(date,event.strip()))
                RemovedDateAcceptEvents[year].pop(len(AcceptEvents[year]) - index - 1)
            if parser.parse(casetime) < parser.parse(date):
                break
    return RemovedDateAcceptEvents


def RemoveInQueueEventByDateFromFile(date, InQueueEvents):
    # print(date)
    if not InQueueEvents:
        return {}
    RemovedDateInQueueEvents = copy.deepcopy(InQueueEvents)
    # print(InQueueEvents)
    for year, events in InQueueEvents.items():
        for index, event in enumerate(InQueueEvents[year][::-1]):
            caseno, severity, queue, casetime = event.split('-~')
            if parser.parse(casetime).strftime("%Y-%m-%d") == date:
                # print("Remove event {} {}".format(len(InQueueEvents[year])-index-1,event))
                RemovedDateInQueueEvents[year].pop(len(InQueueEvents[year]) - index - 1)
            if parser.parse(casetime) < parser.parse(date):
                break
    return RemovedDateInQueueEvents


def SortInQueueEventByTime(CaseInQueueList, date='2020-04-05', debug=True):
    CaseInQueueIndexSortByTime = []
    CaseInQueueSortedAndRemoveList = []
    CaseInQueueSortedRemaingList = [i for i in range(len(CaseInQueueList))]
    CaseInQueueRemoveDupExtSortByTimeList = []
    CaseInqueueRemoveDateSortByTimeList = []

    shift_hour, gmt_hour = GetShiftHour(date)

    for index1, line1 in enumerate(CaseInQueueList):

        smallest_caseno, smallest_priority, smallest_queue, smallest_time = CaseInQueueList[
            CaseInQueueSortedRemaingList[0]].split("-~")
        smallest_datetime = dateutil.parser.parse(smallest_time)
        CaseInQueueIndexSortByTime.append(CaseInQueueSortedRemaingList[0])

        for index2, line2 in enumerate(CaseInQueueList[:]):

            if index2 in CaseInQueueSortedAndRemoveList:
                # if debug:
                #    print("Skip {} {}".format(index1,index2))
                continue
            caseno2, priority2, queue2, time2 = line2.split("-~")
            datetime2 = dateutil.parser.parse(time2)

            # if debug:
            # print("Compare {} {} - {} {}".format(CaseInQueueSortedRemaingList[0],smallest_datetime,index1+index2+1,datetime2))

            if datetime2 < smallest_datetime:
                # if debug:
                # print("Found smaller index{}".format(index2))
                CaseInQueueIndexSortByTime[index1] = index2
                smallest_datetime = datetime2

        # if debug:
        #    print("Iteration {} pop {}".format(index1,CaseInQueueIndexSortByTime[index1]))
        CaseInQueueSortedAndRemoveList.append(CaseInQueueIndexSortByTime[index1])
        CaseInQueueSortedRemaingList.remove(CaseInQueueIndexSortByTime[index1])

        # if debug:
        #    print(CaseInQueueIndexSortByTime)
        #    print(CaseInQueueSortedRemaingList)
        #    print("Sorted Index from CaseInQueueList {}".format(CaseInQueueIndexSortByTime))

    for index in CaseInQueueIndexSortByTime:
        CaseInQueueRemoveDupExtSortByTimeList.append(CaseInQueueList[index])

    if debug:
        print("After Revming Dup Case - to be remoeved DUP FTS/UC")
        for caseline in CaseInQueueRemoveDupExtSortByTimeList:
            print(caseline)
    ###### Remove Dup FTS  List and only keep the last one ######
    ###### Remove Dup UC  List and only keep the last one ######
    ###### Remove Dup Case within 20 seconds and 2 event next to each other and only keep the last one ######
    InQueueFTSList = []  # Index from CaseInQueueRemoveDupExtSortByTimeList #Case , #Timestamp
    InQueueDupFTSIndexList = []
    InQueueUCList = []  # Index from CaseInQueueRemoveDupExtSortByTimeList #Case , #Timestamp
    InQueueDupUCIndexList = []

    LastCaseList = []  # Index from CaseInQueueRemoveDupExtSortByTimeList #Case #Queue #Timestamp
    InQueueDupCaseIndexList = []

    ######## Dup case condidition < 1 minutes
    for index, caseline in enumerate(CaseInQueueRemoveDupExtSortByTimeList):
        caseno, priority, queue, casetime = caseline.split("-~")
        if queue == 'FTS':
            InQueueFTSList.append([index, caseno, casetime])
        elif queue == 'UC':
            InQueueUCList.append([index, caseno, casetime])
        else:
            for LastCase in LastCaseList:
                if LastCase and LastCase[1] == caseno and LastCase[3] == queue:
                    case_datetime = parser.parse(casetime)
                    last_datetime = parser.parse(LastCase[4])
                    ######## Dup case condition ######
                    # 1. same events come in < 60 seconds, 2 events in a row
                    # 2. priority are different , 2 events in a row
                    if (case_datetime - last_datetime).seconds <= 60 or LastCase[2] != priority:
                        if debug:
                            print("Found Dup Case {} {} {}".format(LastCase[0], caseno, LastCase[4]))
                        InQueueDupCaseIndexList.append(LastCase[0])
            LastCaseList.append([index, caseno, priority, queue, casetime])
    InQueueDupCaseIndexList = set(InQueueDupCaseIndexList)

    ###### Get InQueueDupFTSIndexList in order ######
    for index1, fts_case1 in enumerate(InQueueFTSList):
        for index2, fts_case2 in enumerate(InQueueFTSList[index1 + 1:]):
            if fts_case1[1] == fts_case2[1]:
                if debug:
                    print("Dup FTS index {} with {} and remove {}".format(fts_case1[0], fts_case2[0], fts_case1[0]))
                InQueueDupFTSIndexList.append(fts_case1[0])
    ###### Get InQueueDupUCIndexList in order ######
    for index1, uc_case1 in enumerate(InQueueUCList):
        for index2, uc_case2 in enumerate(InQueueUCList[index1 + 1:]):
            if uc_case1[1] == uc_case2[1]:
                if debug:
                    print("Dup UC index {} with {} and remove {}".format(uc_case1[0], uc_case2[0], uc_case1[0]))
                InQueueDupUCIndexList.append(uc_case1[0])
    if debug:
        print("Dup Case List {}".format(" ".join([str(index) for index in InQueueDupCaseIndexList])))
        print("Dup FTS Case List {}".format(" ".join([str(index) for index in set(InQueueDupFTSIndexList)])))
        print("Dup UC Case List {}".format(" ".join([str(index) for index in set(InQueueDupUCIndexList)])))

    InQueueDupIndexList = sorted([*InQueueDupCaseIndexList, *set(InQueueDupFTSIndexList), *set(InQueueDupUCIndexList)])

    for index in InQueueDupIndexList[::-1]:
        CaseInQueueRemoveDupExtSortByTimeList.pop(index)

    ###### Remove Case which is not for that date ######
    for caseline in CaseInQueueRemoveDupExtSortByTimeList:
        caseno, priority, queue, time = caseline.split("-~")
        line_datetime = parser.parse(time)
        if line_datetime.strftime("%Y-%m-%d") == date:
            CaseInqueueRemoveDateSortByTimeList.append(caseline)

    return CaseInqueueRemoveDateSortByTimeList


def UpdWithEngrConvertInQueueEventsByDate(start_date='2020-02-27',
                                          end_date=datetime.datetime.today().strftime("%Y-%m-%d"), shift='apjc',
                                          RawAcceptEventsByDate={}, InQueueEventsByDate={}):
    '''
    1.InQueue Case needs to find the accept engineer and its workgroup
    -- create new key 'AllWithEngr' to write to the same Dict InQueueEventsByDate
    '''

    start_datetime = parser.parse(start_date)
    end_datetime = parser.parse(end_date)
    cur_date = start_date
    cur_datetime = parser.parse(cur_date)

    while cur_datetime.date() <= end_datetime.date():
        cur_date = cur_datetime.strftime("%Y-%m-%d")
        if cur_date not in InQueueEventsByDate.keys():
            cur_datetime = cur_datetime + datetime.timedelta(days=1)
            continue

        ###### Function 1.InQueue Case needs to find the accept engineer and its workgroup ######
        if cur_date not in RawAcceptEventsByDate.keys():
            RawAcceptEventsByDate[cur_date] = {}

        InQueueEventsByDate[cur_date]['AllWithEngr'] = []
        for event in InQueueEventsByDate[cur_date]['All']:
            engr_line = []
            # print("RawEvent-{}".format(event)) #event is in order
            caseno, severity, casetype, casetime = event.split('-~')
            caseno_url = '<a {} href="http://mwz.cisco.com/{}" target="_blank">{}</a>'.format(
                'style="text-decoration:none; color:#0000FF;"', caseno, caseno)
            _, UpdateTime = isOnShift(timestamp=casetime, timezone='GMT', shift=shift)
            event_url = "{}-~{}-~{}-~{}".format(caseno_url, severity, casetype, UpdateTime)
            if caseno in RawAcceptEventsByDate[cur_date].keys():
                # print("CaseNo {} AccBy {}".format(caseno,RawAcceptEventsByDate[date][caseno]))
                # CaseNo 689154452 AccBy [['amikum', 'GCE-ACI-Solutions']]
                one_engr_line = ''
                for engr in RawAcceptEventsByDate[cur_date][caseno]:
                    if engr[1] == "Unknown" or 'FTS_WORKGROUP' in engr[1] or 'UC_WORKGROUP' in engr[1]:
                        # print("Date {} CCO {} WG {}".format(date,engr[0],engr[1]))
                        ccoid, new_wg, date = FindEngrWorkgroup(cur_date, engr[0], RawAcceptEventsByDate)
                        if new_wg != "Unknown":
                            engr[1] = new_wg
                    if not one_engr_line:
                        one_engr_line = one_engr_line + "{}({})".format(engr[0], engr[1])
                    else:
                        one_engr_line = one_engr_line + "-~" + "{}({})".format(engr[0], engr[1])
                engr_line = one_engr_line
                # print(engr_line)
            InQueueEventsByDate[cur_date]['AllWithEngr'].append("{}-~{}".format(event_url, engr_line))
            # print("Appending - UpdEventWithEngr-{}".format(events['AllWithEngr'][-1]))

        cur_datetime = cur_datetime + datetime.timedelta(days=1)

    return InQueueEventsByDate


def UpdateEngrListFromAcceptEventInOrderList(AcceptEventInOrderList, EngrList,
                                             WKGroupList=['APT-ACI-SOLUTIONS', 'APT-ACI-SOLUTIONS2']):
    SYDEngrList = EngrList[0]
    SYDOtherEngrList = EngrList[1]
    BGLEngrList = EngrList[2]
    BGLOtherEngrList = EngrList[3]

    Syd_group_Nname = WKGroupList[0]
    BLR_group_name = WKGroupList[1]

    for caseline in AcceptEventInOrderList:
        caseno, severity, ccoid, workgroup, time = caseline.split("-~")
        if workgroup == "Unknown":
            continue
        if workgroup == Syd_group_Nname:
            if ccoid not in SYDEngrList:
                SYDEngrList.append(ccoid)
                print('Updating {} in SydEngrList'.format(ccoid))
        elif workgroup == BLR_group_name:
            if ccoid not in BGLEngrList:
                print('Updating {} in BGLEngrList'.format(ccoid))
                BGLEngrList.append(ccoid)
                if ccoid in BGLOtherEngrList:
                    print('Removing {} from BGLOtherEngrList'.format(ccoid))
                    BGLOtherEngrList.remove(ccoid)
            elif ccoid in BGLOtherEngrList:
                print('Updating {} in BGLOtherEngrList'.format(ccoid))
                if ccoid in BGLEngrList:
                    print('Removing {} from BGLEngrList'.format(ccoid))
                    BGLEngrList.remove(ccoid)

    return [SYDEngrList, SYDOtherEngrList, BGLEngrList, BGLOtherEngrList]
