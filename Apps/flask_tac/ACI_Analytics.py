import argparse, configparser, datetime, glob, os, pathlib
import pandas as pd
from dateutil import parser
import matplotlib as plt
import ACILib

plt.rcParams.update({'figure.max_open_warning': 0})


def ReadInQueuefile(filename='/home/jovyan/HTTSDashboard/logs/ACI/events/*_InQueueEvent.txt'):
    CaseInQueueFileList = glob.glob(filename)
    # print(CaseInQueueFileList)
    for file in CaseInQueueFileList:
        print('Processing InQueue events from {}'.format(file))
        with open(file, 'r') as f:
            InQueueEvents = f.readlines()
        f.close()
        # print(InQueueEvents[0])
        ###### Add index ######
        InQueueEvents = [[idx, *line.strip().split('-~')] for idx, line in enumerate(InQueueEvents)]
        # print(InQueueEvents[10])

        ###### Split Date-Time to Date and Time columns ######
        InQueueEvents = [[*event, parser.parse(event[4]).strftime("%Y-%m-%d")] for event in InQueueEvents]
        InQueueEvents = [[*event, parser.parse(event[4]).strftime("%H:%M:%S")] for event in InQueueEvents]
        # print(InQueueEvents[10])

        ###### Add Weekdays start from 0(Monday) ######
        InQueueEvents = [[*event, parser.parse(event[4]).weekday()] for event in InQueueEvents]
        # print(InQueueEvents[10])

        pd_labels = ['Idx', 'No', 'Sev', 'Queue', 'DateTime', 'Date', 'Time', 'Weekday']
        df = pd.DataFrame.from_records(InQueueEvents, columns=pd_labels)
        # print(df)
        return df


def ReadAcceptfile(filename='/home/jovyan/HTTSDashboard/logs/ACI/events/*_AcceptEvent.txt'):
    AcceptGlobList = glob.glob(filename)

    SYDEngrList = ACILib.ACI_SYDEngrList
    BGLEngrList = ACILib.ACI_BGLEngrList
    BGLOtherEngrList = ACILib.ACI_BGLOtherEngrList
    SYDOtherEngrList = ACILib.ACI_SYDOtherEngrList

    AcceptEvents = []
    for file in AcceptGlobList:

        print('Processing accept events from {}'.format(file))
        with open(file, 'r') as f:
            AcceptEvents_from_file = f.readlines()
        f.close()

        ###### Update EngrList######
        for idx, line in enumerate(AcceptEvents_from_file):
            caseno, severity, ccoid, workgroup, timestamp = line.strip().split('-~')
            if workgroup == 'APT-ACI-SOLUTIONS' and ccoid not in SYDEngrList:
                print("Appending APT-ACI-SOLUTIONS {}".format(ccoid))
                SYDEngrList.append(ccoid)
            elif workgroup == 'APT-ACI-SOLUTIONS2' and ccoid not in BGLEngrList:
                print("Appending APT-ACI-SOLUTIONS2 {}".format(ccoid))
                BGLEngrList.append(ccoid)
            elif workgroup == 'GCE-ACI-Solutions' and ccoid not in BGLOtherEngrList:
                print("Appending GCE-ACI-Solutions {}".format(ccoid))
                BGLOtherEngrList.append(ccoid)

        ###### Add index ######
        AcceptEvents1 = [[idx, *line.strip().split('-~')] for idx, line in enumerate(AcceptEvents_from_file)]
        # print(AcceptEvents[10])
        # [10, '688521682', '3', 'damistry', 'Unknown', '2020-02-27 01:41:23']

        ###### Split Date-Time to Date and Time columns ######   
        AcceptEvents2 = [[*event, parser.parse(event[5]).strftime("%Y-%m-%d")] for event in AcceptEvents1]
        AcceptEvents3 = [[*event, parser.parse(event[5]).strftime("%H:%M:%S")] for event in AcceptEvents2]
        # print(AcceptEvents[10])
        # [10, '688521682', '3', 'damistry', 'Unknown', '2020-02-27 01:41:23', '2020-02-27', '01:41:23']

        ###### Add Weekdays start from 0(Monday) ######
        AcceptEvents4 = [[*event, parser.parse(event[5]).weekday()] for event in AcceptEvents3]
        # print(AcceptEvents[10])
        # [10, '688521682', '3', 'damistry', 'Unknown', '2020-02-27 01:41:23', '2020-02-27', '01:41:23', 3]
        AcceptEvents = [*AcceptEvents, *AcceptEvents4]

    pd_labels = ['Idx', 'No', 'Sev', 'ccoid', 'Workgroup', 'DateTime', 'Date', 'Time', 'Weekday']
    df = pd.DataFrame.from_records(AcceptEvents, columns=pd_labels)

    ###### Only Onlist Engineer ######
    AllEngrList = set([*SYDEngrList, *BGLEngrList, *BGLOtherEngrList, *SYDOtherEngrList])
    df = df[df['ccoid'].isin(AllEngrList)]

    return df


def AvgCasePerWeekday(df_inqueue_events, df_engr_by_date, start_date, end_date, filename):
    df_cnt_by_weekday = df_inqueue_events.groupby(['Weekday']).agg('count').reset_index()

    df_weekday_cnt = df_inqueue_events.groupby(['Date']).agg('mean').groupby(['Weekday']).agg('count')
    df_weekday_cnt = df_weekday_cnt.reset_index()
    df_weekday_cnt['Weekday'] = df_weekday_cnt['Weekday'].astype('int')

    df_avgcnt_weekdy = df_cnt_by_weekday
    df_avgcnt_weekdy['WeekdayCount'] = df_weekday_cnt['Idx']
    df_avgcnt_weekdy['AvgCaseVol'] = df_avgcnt_weekdy['No'] / df_avgcnt_weekdy['WeekdayCount']
    df_avgcnt_weekdy['AvgCaseVol'].astype('float64')
    df_avgcnt_weekdy['AvgCaseVol'] = df_avgcnt_weekdy['AvgCaseVol'].round(1)

    days = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
    df_avgcnt_weekdy['WeekdayName'] = df_avgcnt_weekdy['Weekday'].apply(lambda x: days[x])

    df_engr_by_date['TotEngrNo'] = df_engr_by_date['BLREngrNo'] + df_engr_by_date['SYDEngrNo']
    df_engr_by_date = df_engr_by_date.groupby('Weekday').agg('sum').reset_index()
    df_engr_by_date = df_engr_by_date.sort_values(by='Weekday').reset_index(drop=True)
    df_avgcnt_weekdy['AvgEngrNo'] = df_engr_by_date['TotEngrNo'] / df_avgcnt_weekdy['WeekdayCount']
    df_avgcnt_weekdy['AvgEngrNo'].astype('float64')
    df_avgcnt_weekdy['AvgEngrNo'] = df_avgcnt_weekdy['AvgEngrNo'].round(1)

    # df_avgcnt_weekdy.plot(kind='bar',x='Weekday',y='AvgCase')
    # ax = df_avgcnt_weekdy[::-1].plot.barh(x='WeekdayName',y='AvgCase',figsize=(5,5),title='AvgCasePerWeekday '+start_date+'-'+end_date)
    ax = df_avgcnt_weekdy.plot(kind='bar', x='WeekdayName', y=['AvgCaseVol', 'AvgEngrNo'], figsize=(5, 5),
                               title='AvgCasePerWeekday ' + start_date + '-' + end_date)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.get_figure().savefig(filename, bbox_inches='tight', pad_inches=0)


def TotCase(df, start_date, end_date, filenames=[]):
    # Total Case Stacking by workgroup
    df_totcase_wg_2 = df.groupby(['Date', 'Queue'], as_index=False).size().unstack().fillna(0)
    df_totcase_wg_2.plot(kind='bar', stacked=True, figsize=(15, 5),
                         title='Total InQueue Case ' + start_date + '-' + end_date).get_figure().savefig(filenames[0],
                                                                                                         bbox_inches='tight',
                                                                                                         pad_inches=0)

    # Total case stacking by workgroup SYD and BLR only
    df_totcase_wg_3 = df.groupby(['Date', 'Queue'], as_index=False).size().unstack().fillna(0)
    df_totcase_wg_3[['CX-APJC-BLR-ACI-SSPT', 'CX-APJC-SYD-ACI-SSPT']].plot.area(stacked=False, figsize=(15, 5),
                                                                                title='InQueue Case Volume BLR/SYD ' + start_date + '-' + end_date).get_figure().savefig(
        filenames[1], bbox_inches='tight', pad_inches=0)

    # LB Ratio
    df_totcase_wg_3_2 = df.groupby(['Date', 'Queue'], as_index=False).size().unstack().fillna(0)
    # df_totcase_wg_3_2 = df_totcase_wg_3_2.drop(['FTS','UC','WW-Rakuten-ACI','WW-ACI-Solutions'],axis=1)
    df_totcase_wg_3_2 = df_totcase_wg_3_2[['CX-APJC-BLR-ACI-SSPT', 'CX-APJC-SYD-ACI-SSPT']]
    df_totcase_wg_3_2 = df_totcase_wg_3_2.reset_index()
    df_totcase_wg_3_2['Ratio'] = df_totcase_wg_3_2['CX-APJC-BLR-ACI-SSPT'] / (
            df_totcase_wg_3_2['CX-APJC-SYD-ACI-SSPT'] + 0.0001)
    df_totcase_wg_3_2[df_totcase_wg_3_2['Ratio'] < 100].plot.area(x='Date', y='Ratio', figsize=(15, 5),
                                                                  title='BLR/SYD InQueue LB Actual Ratio ' + start_date + '-' + end_date,
                                                                  grid=True).get_figure().savefig(filenames[2],
                                                                                                  bbox_inches='tight',
                                                                                                  pad_inches=0)


def DFCasePerHourByDate(df_new, df_raw, start_hour=0, date='2020-04-05'):
    df_1day = df_raw[df_raw['Date'].between(date, date, inclusive=True)]
    # how many days in the selected date
    # days17 = df_1day.groupby(['Date']).agg('mean').groupby(['Weekday']).agg('count').sum()['Idx']
    # How many cases in selected hours
    if start_hour == 0:
        cv1 = df_1day[df_1day['Time'].between('00:00:00', '00:59:59', inclusive=True)].count()['Idx']
        cv2 = df_1day[df_1day['Time'].between('01:00:00', '01:59:59', inclusive=True)].count()['Idx']
        cv3 = df_1day[df_1day['Time'].between('02:00:00', '02:59:59', inclusive=True)].count()['Idx']
        cv4 = df_1day[df_1day['Time'].between('03:00:00', '03:59:59', inclusive=True)].count()['Idx']
        cv5 = df_1day[df_1day['Time'].between('04:00:00', '04:59:59', inclusive=True)].count()['Idx']
        cv6 = df_1day[df_1day['Time'].between('05:00:00', '05:59:59', inclusive=True)].count()['Idx']
    elif start_hour == 1:
        cv1 = df_1day[df_1day['Time'].between('01:00:00', '01:59:59', inclusive=True)].count()['Idx']
        cv2 = df_1day[df_1day['Time'].between('02:00:00', '02:59:59', inclusive=True)].count()['Idx']
        cv3 = df_1day[df_1day['Time'].between('03:00:00', '03:59:59', inclusive=True)].count()['Idx']
        cv4 = df_1day[df_1day['Time'].between('04:00:00', '04:59:59', inclusive=True)].count()['Idx']
        cv5 = df_1day[df_1day['Time'].between('05:00:00', '05:59:59', inclusive=True)].count()['Idx']
        cv6 = df_1day[df_1day['Time'].between('06:00:00', '06:59:59', inclusive=True)].count()['Idx']

    Case_per_day = [date, parser.parse(date).weekday(), cv1, cv2, cv3, cv4, cv5, cv6]
    df_new = df_new.append(pd.Series(Case_per_day, index=df_new.columns), ignore_index=True)

    return df_new


def CasePerHour(df, start_date, end_date, filenames=[]):
    # finename0 : Case Taken Per Engineer
    # filename1 : Onshift Engineer per day

    # Initialize new dataframe
    col_names = ['Date', 'Weekday', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6']
    df_case_by_hour = pd.DataFrame(columns=col_names)

    cur_datetime = parser.parse(start_date)
    end_datetime = parser.parse(end_date)

    while cur_datetime <= end_datetime:
        shift_hour, gmt_hour = ACILib.GetShiftHour(start_date)
        # print("Processing ... {}".format(cur_datetime.strftime("%Y-%m-%d")))
        # print(df_case_by_hour)
        df_case_by_hour = DFCasePerHourByDate(df_case_by_hour, df, start_hour=shift_hour[0],
                                              date=cur_datetime.strftime("%Y-%m-%d"))
        cur_datetime = cur_datetime + datetime.timedelta(days=1)

    df_case_by_hour['H123'] = df_case_by_hour['H1'] + df_case_by_hour['H2'] + df_case_by_hour['H3']
    df_case_by_hour['H456'] = df_case_by_hour['H4'] + df_case_by_hour['H5'] + df_case_by_hour['H6']

    df_case_by_hour.set_index('Date').plot.area(y=['H1', 'H2', 'H3', 'H4', 'H5', 'H6'], figsize=(15, 5), stacked=True,
                                                title='Case Volume per hour ' + start_date + '-' + end_date).get_figure().savefig(
        filenames[0], bbox_inches='tight', pad_inches=0)
    df_case_by_hour.set_index('Date').plot(y=['H123', 'H456'], figsize=(15, 5), kind='bar', stacked=True,
                                           title='Case Volume per 3 hours ' + start_date + '-' + end_date).get_figure().savefig(
        filenames[1], bbox_inches='tight', pad_inches=0)


def AvgTakenCasePerEngr(df, start_date, end_date, filenames=[]):
    df = df[df['Date'].between(start_date, end_date, inclusive=True)]

    df_BLR_all = df[df['ccoid'].isin([*ACILib.ACI_BGLEngrList, *ACILib.ACI_BGLOtherEngrList])]
    df_SYD_all = df[df['ccoid'].isin([*ACILib.ACI_SYDEngrList, *ACILib.ACI_SYDOtherEngrList])]

    ###### Generating BRL Case Per Engineer Per day ######
    df_BLR_CasePerDay = df_BLR_all.groupby(['Date']).agg('count')['No'].reset_index()
    df_BLR_CasePerDay.rename(columns={'Date': 'Date', 'No': 'BLRCaseNo'}, inplace=True)
    df_BLR_engr_by_date = df_BLR_all.groupby('Date')['ccoid'].unique().to_frame()
    df_BLR_engr_by_date.rename(columns={'Date': 'Date', 'ccoid': 'BLRccoidList'}, inplace=True)
    df_BLR_engr_by_date = df_BLR_engr_by_date.reset_index()
    df_BLR_engr_by_date['Date'] = pd.to_datetime(df_BLR_engr_by_date['Date']).dt.date
    df_BLR_engr_by_date['Weekday'] = pd.to_datetime(df_BLR_engr_by_date['Date']).dt.dayofweek
    df_BLR_engr_by_date['BLREngrNo'] = df_BLR_engr_by_date['BLRccoidList'].str.len().to_frame()

    ###### Generating SYD Case Per Engineer Per Day ######
    df_SYD_CasePerDay = df_SYD_all.groupby(['Date']).agg('count')['No'].reset_index()
    df_SYD_CasePerDay.rename(columns={'Date': 'Date', 'No': 'SYDCaseNo'}, inplace=True)
    df_SYD_engr_by_date = df_SYD_all.groupby('Date')['ccoid'].unique().to_frame()
    df_SYD_engr_by_date.rename(columns={'Date': 'Date', 'ccoid': 'SYDccoidList'}, inplace=True)
    df_SYD_engr_by_date = df_SYD_engr_by_date.reset_index()
    df_SYD_engr_by_date['Date'] = pd.to_datetime(df_SYD_engr_by_date['Date']).dt.date
    df_SYD_engr_by_date['Weekday'] = pd.to_datetime(df_SYD_engr_by_date['Date']).dt.dayofweek
    ###### Anlyzing weekdays and weekend seperately ######
    df_SYD_engr_by_weekday = df_SYD_engr_by_date[
        (df_SYD_engr_by_date['Weekday'] != 5) & (df_SYD_engr_by_date['Weekday'] != 6)]
    df_SYD_engr_by_weekend = df_SYD_engr_by_date[
        (df_SYD_engr_by_date['Weekday'] == 5) | (df_SYD_engr_by_date['Weekday'] == 6)]

    ###### Removing SYD_Other from Weekday ######
    def remove_syd_other(ccoid_list):
        SYDOtherEngrList = ['zdazhi', 'zmeng']
        new_list = [ccoid for ccoid in ccoid_list if ccoid not in SYDOtherEngrList]
        return new_list

    df_SYD_engr_by_weekday['SYDccoidListClean'] = df_SYD_engr_by_weekday['SYDccoidList'].apply(remove_syd_other)
    df_SYD_engr_by_weekday['ccoid'] = df_SYD_engr_by_weekday['SYDccoidListClean'].str.len().to_frame()
    df_SYD_engr_by_weekday.rename(columns={'Date': 'Date', 'ccoid': 'SYDEngrNo'}, inplace=True)
    df_SYD_engr_by_weekend['SYDEngrNo'] = df_SYD_engr_by_weekend['SYDccoidList'].str.len().to_frame()
    df_SYD_engr_by_date_2 = pd.concat([df_SYD_engr_by_weekday[['Date', 'SYDEngrNo', 'Weekday']],
                                       df_SYD_engr_by_weekend[['Date', 'SYDEngrNo', 'Weekday']]])
    df_SYD_engr_by_date_2 = df_SYD_engr_by_date_2.sort_values(by="Date")

    ###### Contacting SYD BLR Engr No ######
    df_engr_by_date = pd.concat([df_BLR_engr_by_date[['BLREngrNo']], df_SYD_engr_by_date_2],
                                axis=1, ignore_index=True, sort=True)
    df_engr_by_date.rename(columns={0: 'BLREngrNo', 1: 'Date', 2: 'SYDEngrNo', 3: 'Weekday'}, inplace=True)
    df_engr_by_date.plot.area(x='Date', y=['BLREngrNo', 'SYDEngrNo'], figsize=[15, 5], stacked=False,
                              title='Onshift Engineer ' + start_date + '-' + end_date).get_figure().savefig(
        filenames[1], bbox_inches='tight', pad_inches=0)

    ##### Contacting SYD BLR ######
    df_BLR_case_engr = pd.concat([df_BLR_CasePerDay, df_BLR_engr_by_date], axis=1, ignore_index=True, sort=True)
    df_BLR_case_engr = df_BLR_case_engr.drop([2, 3], axis=1)
    df_BLR_case_engr.rename(columns={0: 'Date', 1: 'BLRCaseNo', 4: 'Weekday', 5: 'BLREngrNo'}, inplace=True)
    df_BLR_case_engr['BLRCaseNo'].astype('float64')
    df_BLR_case_engr['BLREngrNo'].astype('float64')
    df_BLR_case_engr['BLRCasePerEngr'] = (df_BLR_case_engr['BLRCaseNo'] / df_BLR_case_engr['BLREngrNo']).round(2)

    df_SYD_case_engr = pd.concat([df_SYD_CasePerDay, df_SYD_engr_by_date_2], axis=1, ignore_index=True, sort=True)
    df_SYD_case_engr = df_SYD_case_engr.drop([2], axis=1)
    df_SYD_case_engr.rename(columns={0: 'Date', 1: 'SYDCaseNo', 3: 'SYDEngrNo', 4: 'Weekday'}, inplace=True)
    df_SYD_case_engr['SYDCaseNo'].astype('float64')
    df_SYD_case_engr['SYDEngrNo'].astype('float64')
    df_SYD_case_engr['SYDCasePerEngr'] = (df_SYD_case_engr['SYDCaseNo'] / df_SYD_case_engr['SYDEngrNo']).round(2)

    ###### Average case per engineer and plotting ######
    df_caseperengr_compare = pd.concat([df_SYD_case_engr, df_BLR_case_engr], axis=1, ignore_index=True, sort=True)
    df_caseperengr_compare = df_caseperengr_compare.drop([5, 3], axis=1)
    df_caseperengr_compare.rename(
        columns={0: 'Date', 1: 'SYDCaseNo', 2: 'SYDEngrNo', 4: 'SYDCasePerEngr', 6: 'BLRCaseNo', 7: 'Weekday',
                 8: 'BLREngrNo', 9: 'BLRCasePerEngr'}, inplace=True)

    df_caseperengr_compare.plot.area(x='Date', y=['BLRCasePerEngr', 'SYDCasePerEngr'], figsize=[15, 5],
                                     title='Case Taken Per Engineer ' + start_date + '-' + end_date,
                                     stacked=False).get_figure().savefig(filenames[0], bbox_inches='tight',
                                                                         pad_inches=0)

    medianprops = dict(linestyle='-', linewidth=2.5, color='firebrick')
    ax = df_caseperengr_compare.plot(kind='box', x='Date', y=['SYDCasePerEngr', 'BLRCasePerEngr'], figsize=[5, 5],
                                     title='CasePerEngrBox ' + start_date + '-' + end_date, stacked=False, grid=True,
                                     medianprops=medianprops)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.get_figure().savefig(filenames[2], bbox_inches='tight', pad_inches=0)

    return df_engr_by_date


def main(start_date, end_date, force_overwrite=False):
    config = configparser.ConfigParser()
    config.read('./flask_tac/tacconfig.ini')
    shift = 'apjc'
    tech_strip = 'aci'
    event_path = config[shift]['_'.join(['eventpath', tech_strip.upper()])]
    analytics_path = config[shift]['_'.join(['analytics', tech_strip.upper()])]

    flask_container_path = ''
    current_container_path = flask_container_path
    accept_filename = current_container_path + event_path + '*_AcceptEvent.txt'
    df_accept_events = glob.glob(accept_filename)
    inqueue_filename = current_container_path + event_path + '*_InQueueEvent.txt'
    df_inqueue_events = glob.glob(inqueue_filename)

    print("Analystics on InQueue:{} Accept:{}".format(inqueue_filename, accept_filename))

    df_inqueue_events = ReadInQueuefile(inqueue_filename)
    df_accept_events = ReadAcceptfile(accept_filename)

    df_inqueue_events = df_inqueue_events[df_inqueue_events['Date'].between(start_date, end_date, inclusive=True)]

    # Create report directory
    # analytics_path = '/HTTSDashboard/logs/ACI/analytics/'
    analytics_path = analytics_path + start_date + "_" + end_date + '/'
    if os.path.isdir(analytics_path):
        if force_overwrite:
            print("{} anlytics directory exists, force_to_overwrite.".format(analytics_path))
        else:
            print("{} anlytics directory exists, return.".format(analytics_path))
            return
    else:
        pathlib.Path(analytics_path).mkdir(parents=True, mode=775, exist_ok=True)
        # os.mkdir(analytics_path)
        print("Creating analytics directory {}".format(analytics_path))

    # Generate TotCase plot
    filename_totcase_all_queue = analytics_path + 'Total_Case_All_Queues.png'
    filename_totcase_syd_blr = analytics_path + 'Total_Case_SYD_BLR.png'
    filename_totcase_syd_blr_ratio = analytics_path + 'Total_Case_SYD_BLR_Ratio.png'
    # print("Generating Total Case Volume per day {} {}".format(filename_totcase_all_queue,filename_totcase_syd_blr))

    TotCase(df_inqueue_events, start_date, end_date,
            [filename_totcase_all_queue, filename_totcase_syd_blr, filename_totcase_syd_blr_ratio])

    # Case By Hour
    filename_caseperhour = analytics_path + 'Case_Per_Hour.png'
    filename_caseper3hours = analytics_path + 'Case_Per_3Hours.png'

    # print("Generating Case Per Hour {}".format(filename_caseperhour))
    CasePerHour(df_inqueue_events, start_date, end_date, [filename_caseperhour, filename_caseper3hours])

    # Case Taken Per Engineer
    filename_caseperengr = analytics_path + 'Case_Taken_Per_Engr.png'
    filename_caseperengr_box = analytics_path + 'Case_Taken_Per_Engr_Box.png'
    filename_onshiftengr = analytics_path + 'OnShift_Engineer.png'
    df_engr_by_date = AvgTakenCasePerEngr(df_accept_events, start_date, end_date,
                                          [filename_caseperengr, filename_onshiftengr, filename_caseperengr_box])

    # Generate AvgCasePerWeekday plot
    filename_caseperweekday = analytics_path + 'Case_Per_Weekday.png'
    # print("Generating Case Per Weekday {}".format(filename_caseperweekday))
    AvgCasePerWeekday(df_inqueue_events, df_engr_by_date, start_date, end_date, filename_caseperweekday)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-s', action='store', dest='start_date', default='2020-02-27', help='Start date to parse')
    argparser.add_argument('-e', action='store', dest='end_date',
                           default=datetime.datetime.today().strftime("%Y-%m-%d"), type=str, help='End date to parse')
    argparser.add_argument('--force_overwrite', action='store_true',
                           help="Force to overwrite the analytics even it exists")

    argresult = argparser.parse_args()

    start_date = argresult.start_date
    end_date = argresult.end_date
    force_overwrite = argresult.force_overwrite

    if force_overwrite:
        print("Analytics Period {} - {} - Force to overwrite.".format(start_date, end_date))
    else:
        print("Analytics Period {} - {} - No overwrite.".format(start_date, end_date))

    main(start_date, end_date, force_overwrite=force_overwrite)
