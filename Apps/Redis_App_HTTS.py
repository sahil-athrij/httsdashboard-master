import redis , datetime, time
import CommonLib
import csv
from webexteamssdk import WebexTeamsAPI
import WbxTeams
import configparser
import pytz
from pytz import timezone

#Reading current config from file
config = configparser.ConfigParser()
config.read('config.ini')

#Logger Initialization
logger_file = "Redis_HTTS_App.log"
logger = CommonLib.HTTSLogger(name=__file__,logfile=logger_file,logfilepath=config['Logging']['LoggingPath'])

#Redis Initialization
Redis_HTTS_Pool = redis.ConnectionPool(host=config['Redis']['ServerIP'], port=config['Redis']['ServerPort'],db=config['Redis']['HTTSDB'])
Redis_HTTS = redis.StrictRedis(connection_pool=Redis_HTTS_Pool)
Redis_TAC_Pool = redis.ConnectionPool(host=config['Redis']['ServerIP'], port=config['Redis']['ServerPort'],db=config['Redis']['TACDB'])
Redis_TAC = redis.StrictRedis(connection_pool=Redis_TAC_Pool)
Redis_DB = Redis_HTTS

#CSOne GCI Authentication/Cookie Initialization
CSOneSession = CommonLib.CSOneSession(logger=CommonLib.HTTSLogger(name="GetGCI",logfile="GetGCI-HTTS-App.log",logfilepath=config['Logging']['LoggingPath']),debug=True)

#WebexTeams Initialization
sydney_local_timezone = timezone('Australia/Sydney')
isSentToSydneyHTTS = False
isSentToCBATeam = False
wbx_max_chr = 500
webexteamsapi_htts = WebexTeamsAPI(access_token=config['WebexTeams']['bot_token_htts'])
wbx_markdown_hyperlinks = "{}([eportal](https://eportal.cisco.com/#/public/account/{}/gr/overall)), SR [{}](http://mwz.cisco.com/{}), "
InQueueMinuteAlert = {
    '1':[int(min) for min in config['Case']['P1_Alert_Minute'].split(',')],
    '2':[int(min) for min in config['Case']['P2_Alert_Minute'].split(',')],
    '3':[int(min) for min in config['Case']['P3_Alert_Minute'].split(',')],
    '4':[int(min) for min in config['Case']['P4_Alert_Minute'].split(',')],
}

PollingTime = int(config['Redis']['PollingTime'])
CaseProcessedState = {}

print("================================")
print("Polling Time:{} seconds.".format(PollingTime))
print("Redis IP {} Port {} DB {}".format(config['Redis']['ServerIP'],config['Redis']['ServerPort'],config['Redis']['HTTSDB']))
print("Logging: container:{} host:{} file:{}".format(config['Logging']['LoggingPath'],'/HTTSDashboard/logs',logger_file))
for severity,minutes in InQueueMinuteAlert.items():
    print("P{} InQueue Alert to WebexTeams at {} minute".format(severity," ".join([str(min) for min in minutes])))
#print("CSOne Authencation Succeeds") if isCSoneLoggedIn else print("CSOne Authentication Failure")
print("================================")

while True:
    
    ###### All variables used for the loop claimed here ######
    logger_string = ""
    markdown = ""
    case_stripe = ""
    webexteams_msgs = []
    pd = ""
    cs = ""
    ap = ""
    card = WbxTeams.Card()
    CustomerDic =  CommonLib.read_csv(config['Customer']['CustomerList'], "PortfolioID", ",")
    WbxRoomDic = CommonLib.read_csv(config['WebexTeams']['WbxRoomList'], "Stripe", ",")
    case_status_dic = {} #{"caseno":["Accepted",0,"InQueue",1]} 0,1 is event number from all_cases below
    skip_case = [] #Delete from Queue and no need for 2nd iteration.
    
    all_cases = [case.decode() for case in Redis_DB.keys()]
    
    for case in all_cases:
        case_status_dic[case] = []
        
    if len(all_cases) >= 1:
        logger_string = logger_string+"There are {} events in RedisDB {}\n".format(len(Redis_DB.keys())," ".join(all_cases))
    else:
        time.sleep(PollingTime)
        continue
    
    ##### 1st Iteration - parsing ######
    #If Accepted the case within 1 minute, there might be the issue Accepted before InQueue from BORG, thus parsing first
    #17th Feb 2020 Adding GCI in the 1st Iteration.
    for eventno, case in enumerate(all_cases):
        
        #Redis itself only have one pair of key/value for a case (as a key)
        #Any event comes in for the same case will be overwritten by the latest even, if InQueue comes in later than Accept, than it will create issue.
        #In order to resolve it
        #1. use delay to process the accept event in case InQueue after that(Delayed_Process_Minute)
        #2. create the below time from rabbitmq indicates the exact time of the event.
        #2.1 Case_InQueue_Time,Case_Accepted_TimeCase_Dispatched_Time
        
        CaseDic = Redis_DB.hgetall(case) #in binary format due to Redis
        #TODO: proper conversion
        try:
            CaseDic = { y.decode('utf-8'): CaseDic.get(y).decode('utf-8') for y in CaseDic.keys() } #Converting Redis byte String Dict to String Dictionary
        except Exception as e:
            print(e, CaseDic)
            pass

        isInQueue = False
        isAccepted = False
        isDispatched = False
        
        if 'Case_InQueue_Time' in CaseDic.keys():
            case_status_dic[case].append("InQueue")
            case_status_dic[case].append(str(eventno))
            isInQueue = True
            
        if 'Case_Accepted_Time' in CaseDic.keys():
            case_status_dic[case].append("Accepted")
            case_status_dic[case].append(str(eventno))
            isAccepted = True
            
        if 'Case_Dispatched_Time' in CaseDic.keys():
            case_status_dic[case].append("Dispatched")
            case_status_dic[case].append(str(eventno))
            isDispatched = True
            
        #If the case is not InQueue/Accept/Dispatched then delete
        #Protection code(it may not happen): sometimes only GCI exists which is wrong.
        if not isInQueue and not isAccepted and not isDispatched:
            logger_string = logger_string+"Exception: Skipping/Deleting case {} from RedisDB\n".format(case)
            skip_case.append(case)
            Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())
            Redis_DB.delete(case)
            continue
            
        #17th Feb 2020 Adding GCI in the 1st Iteration.
        if case not in skip_case and 'Customer_Symptom' not in CaseDic.keys():
            try:
                Redis_DB.hmset(case,CSOneSession.CSOneGetGCI(case))
            except:
                continue 
                
    ###### 2nd Iteration - Case handling ######
    for case,status in case_status_dic.items():
        
        logger_string=logger_string+"Processing {} - {}\n".format(case," ".join(status))
        if case in skip_case:
            logger_string=logger_string+"2nd Iteration Skip case {}\n".format(case)
            continue
            
        CaseDic = Redis_DB.hgetall(case)
        
        #Store case processed state, if case not in the CaseProcessedState dict, it is the first time to be processed
        if case in CaseProcessedState:
            CaseProcessedState[case] = True
            logger_string=logger_string+"{} is in {}, so it already processed".format(case,CaseProcessedState)
        else:
            logger_string=logger_string+"{} is not in {}, adding it in CaseProcessedState".format(case,CaseProcessedState)
            CaseProcessedState.update({case : False})

        #TODO: proper conversion
        try:
            CaseDic = { y.decode('utf-8'): CaseDic.get(y).decode('utf-8') for y in CaseDic.keys() } #Converting to String Dictionary
        except Exception as e:
            print(e, CaseDic)
            pass
        
        #Please refer to RabbitMQ 3rd Feb 2020 comment manually overwite the case status to Accepted
        #it can only be done in the 2nd iteration as CaseDic will be regenerated and overwritten.
        #logger_string = logger_string+"CaseDic {}\n".format(" ".join([key+":"+value for key,value in CaseDic.items()]))
        if 'Case_Accepted_Time' in CaseDic.keys():
            logger_string = logger_string+"Manually change the status to Case_Accepted from {}\n".format(CaseDic['Case_Status'])
            CaseDic['Case_Status'] = 'Case_Accepted'
                
        #Initialize all variables.
        case_inqueue_time_datetime = datetime.datetime.now() - datetime.timedelta(days=1)
        InQueueSeconds = -1
        InQueueMinutes = -1
        AcceptSeconds = -1
        AcceptMinutes = -1
        AcceptSecondsTillNow = -1
        AcceptMinutesTillNow = -1
        WbxCardDisplayed = 0
        
        if 'Case_InQueue_Time' in CaseDic.keys():
            case_inqueue_time_datetime = datetime.datetime.strptime(CaseDic['Case_InQueue_Time'], '%Y-%m-%d %H:%M:%S')
            InQueueSeconds = int((datetime.datetime.now() - case_inqueue_time_datetime).total_seconds())
            InQueueMinutes = int(InQueueSeconds/60)
        if 'Case_Accepted_Time' in CaseDic.keys():
            case_accepted_time_datetime =  datetime.datetime.strptime(CaseDic['Case_Accepted_Time'], '%Y-%m-%d %H:%M:%S')
            AcceptSeconds = int((case_accepted_time_datetime - case_inqueue_time_datetime).total_seconds())
            AcceptMinutes = int(AcceptSeconds/60)
            AcceptSecondsTillNow = int((datetime.datetime.now() - case_accepted_time_datetime).total_seconds())
            AcceptMinutesTillNow = int(AcceptSecondsTillNow/60)

        #set up Notification for CBA Team when PorfolioID is CBA - DCN or CBA - NPS:
        if CaseDic['PortfolioID'] == '4262581' or CaseDic['PortfolioID'] == '4119582' or CaseDic['PortfolioID'] == '4067291':
            isSentToCBATeam = True
        else:
            isSentToCBATeam = False
    
        ######Case logic handling ######
        
        ###### Dispatched Event ######
        if 'Dispatched' in case_status_dic[case]:
            isSentToSydneyHTTS = False
            logger_string = logger_string+"Deleting {} Case {} from RedisDB as it's dispatched...\n".format(CustomerDic[CaseDic['PortfolioID']]['AccountName'],case)
            try:
                case_stripe = CommonLib.Tech_Stripe(CaseDic['Tech'],CaseDic['SubTech'],CaseDic['Title'],CaseDic['ProductFamily'])
            except Exception as e:
                print(e, CaseDic)
                pass
            markdown = "[{} {}](http://mwz.cisco.com/{}) P{} {} is **Scheduled Dispatched** at {}  \n".format(CustomerDic[CaseDic['PortfolioID']]['AccountName'],case,case,\
                CaseDic['Severity'],CaseDic['Title'],CaseDic['Case_Dispatched_Time'])
            
            webexteams_msgs.append({"stripe" : case_stripe, "webexteams_markdown" : markdown})
            del CaseProcessedState[case]
            Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())
            Redis_DB.delete(case)
        
        ###### Case is InQueue and Case is Accepted ######
        elif 'InQueue' in case_status_dic[case] and 'Accepted' in case_status_dic[case]:

            #FTS use alias for case taker, Requeu use Owner for case taker.
            ActualCaseTaker = ''
            if 'Case_Accepted' in CaseDic['Case_Status']:
                #ActualCaseTaker = CaseDic['Owner']
                ActualCaseTaker = CaseDic['Case_Accepted_Owner']
            elif 'FTS_Accepted' in CaseDic['Case_Status']:
                ActualCaseTaker = CaseDic['Alias']
                
            logger_string = logger_string+"IA {} {}mins [{} {}](http://mwz.cisco.com/{}) P{} is taken by {} {} at {}\n".format(\
                CaseDic['Case_Status'],AcceptMinutes,CustomerDic[CaseDic['PortfolioID']]['AccountName'],case,case,CaseDic['Severity'],ActualCaseTaker,CaseDic['Case_Accepted_Workgroup'],\
                CaseDic['Case_Accepted_Time'])

            #sydhttsroot@syd-htts-dashboard:~/HTTSDashboard/logs$ egrep "688172887" RabbitMQ_HTTS_Event.log 
            #MQToRedis:688172887 3 Case_Accepted_Leaked_Eng NULL 9k running time Memory low (15% is unused) by ahanjer at 2020-01-02 05:44:47
            #MQToRedis:688172887 3 Case_InQueue_Leaked_AH HTTS-WW-DCSW 9k running time Memory low (15% is unused) by NULL at 2020-01-02 05:44:20
            #As per the above log, if Accepted before InQueue(From BORG) it will create isue with the event, use Delayed_Process_Minute to avoid this
            
            if AcceptMinutesTillNow > int(config['Case']['Delayed_Process_Minute']):
                dt_utc_Case_Accept_Time = datetime.datetime.strptime(CaseDic['Case_Accepted_Time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
                Case_Accepted_Time_Local = dt_utc_Case_Accept_Time.astimezone(sydney_local_timezone).strftime("%H:%M:%S %d %b %Y %Z%z")
                #Wbx Notification for Case Accepted
                if CommonLib.isOnShift(sydney_local_timezone,CaseDic['ModDateUTC']):
                    isSentToSydneyHTTS = True
                else:
                    isSentToSydneyHTTS = False    
                try:
                    case_stripe = CommonLib.Tech_Stripe(CaseDic['Tech'],CaseDic['SubTech'],CaseDic['Title'],CaseDic['ProductFamily'])
                except Exception as e:
                    print(e, CaseDic)
                    pass
                
                markdown = "**{}** ".format(CaseDic['Case_Status'][:13]) + \
                wbx_markdown_hyperlinks.format(CustomerDic[CaseDic['PortfolioID']]['AccountName'],CustomerDic[CaseDic['PortfolioID']]['EportalID'],case,case)+ \
                "P{} Title: '{}' has been taken by {} in {} at {} \n\n".format(CaseDic['Severity'],CaseDic['Title'],ActualCaseTaker,CaseDic['Case_Accepted_Workgroup'],Case_Accepted_Time_Local)
                gci_markdown = ""
                webexteams_msgs.append({"stripe" : case_stripe, "webexteams_markdown" : markdown, "webexteams_gci" : gci_markdown})
                
                logger_string = logger_string+"Deleting {} Case {} from RedisDB as it's accepted.\n".format(CustomerDic[CaseDic['PortfolioID']]['AccountName'],case)
                del CaseProcessedState[case]
                Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())
                Redis_DB.delete(case)
        
        ###### Case Yank or Assignment = Case InQueue event is not there while case is accepted ######
        elif 'InQueue' not in case_status_dic[case] and 'Accepted' in case_status_dic[case]:
            
            logger_string = logger_string+"Exception {}mins [{} {}](http://mwz.cisco.com/{}) P{} {} is AcptNoInQueue time. Yank or Assignment\n".format(AcceptMinutes,CustomerDic[CaseDic['PortfolioID']]['AccountName'],case,case,CaseDic['Severity'],CaseDic['Queue'])
            
            if AcceptMinutesTillNow > int(config['Case']['Delayed_Process_Minute']) or AcceptMinutesTillNow == -1:
                logger_string = logger_string+"Deleting {} {} {} after {}mins in RedisDB as AcptNoInQueue...Yank or Assignment\n".format(\
                    CustomerDic[CaseDic['PortfolioID']]['AccountName'],case,CaseDic['Title'],AcceptMinutesTillNow)
                #Wbx Notification for Case Yanked or Assignemnt
                if CommonLib.isOnShift(sydney_local_timezone,CaseDic['ModDateUTC']):
                    isSentToSydneyHTTS = True
                else:
                    isSentToSydneyHTTS = False
                
                try:
                    case_stripe = CommonLib.Tech_Stripe(CaseDic['Tech'],CaseDic['SubTech'],CaseDic['Title'],CaseDic['ProductFamily'])
                except Exception as e:
                    print(e, CaseDic)
                    pass
                
                markdown = wbx_markdown_hyperlinks.format(CustomerDic[CaseDic['PortfolioID']]['AccountName'],CustomerDic[CaseDic['PortfolioID']]['EportalID'],case,case) + "P{} Title: '{}' is yanked by or assigned to {} in {}\n\n".format(CaseDic['Severity'],CaseDic['Title'],CaseDic['Owner'], CaseDic['Case_Accepted_Workgroup'])
                gci_markdown = ""
                webexteams_msgs.append({"stripe" : case_stripe, "webexteams_markdown" : markdown, "webexteams_gci" : gci_markdown})
                del CaseProcessedState[case]
                Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())
                Redis_DB.delete(case)
                
        ###### Case InQueue event there while not been accepted ######
        elif 'InQueue' in case_status_dic[case] and 'Accepted' not in case_status_dic[case]:
            dt_utc_Case_InQueue_Time = datetime.datetime.strptime(CaseDic['Case_InQueue_Time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
            Case_Inqueue_Time_Local = dt_utc_Case_InQueue_Time.astimezone(sydney_local_timezone).strftime("%H:%M:%S %d %b %Y %Z%z")
            logger_string = logger_string+"I {} {}mins [{}](http://mwz.cisco.com/{}) P{} {} InQueue {} at {}\n".format(\
                CaseDic['Case_Status'],InQueueMinutes,case,case,CaseDic['Severity'],CaseDic['Title'],CaseDic['Queue'],\
                CaseDic['Case_InQueue_Time'])
            
            if InQueueMinutes in InQueueMinuteAlert[CaseDic['Severity']] or CaseProcessedState[case] == False:
                #Wbx Notification for Case in Queue
                if CommonLib.isOnShift(sydney_local_timezone,CaseDic['ModDateUTC']):
                    isSentToSydneyHTTS = True
                else:
                    isSentToSydneyHTTS = False
                
                try:
                    case_stripe = CommonLib.Tech_Stripe(CaseDic['Tech'],CaseDic['SubTech'],CaseDic['Title'],CaseDic['ProductFamily'])
                except Exception as e:
                    print(e, CaseDic)
                    pass
                
                markdown = "**{}** for **{}mins** ".format(CaseDic['Case_Status'][:12],InQueueMinutes) + \
                wbx_markdown_hyperlinks.format(CustomerDic[CaseDic['PortfolioID']]['AccountName'],CustomerDic[CaseDic['PortfolioID']]['EportalID'],case,case)+\
                 "P{} Tech:'{}', SubTech:'{}', Title: '{}', dispatched to {} at {} \n\n".format(CaseDic['Severity'],CaseDic['Tech'],CaseDic['SubTech'],CaseDic['Title'],CaseDic['Queue'],Case_Inqueue_Time_Local)

                if CaseProcessedState[case] == False:
                    if CaseDic['Problem_Description'] == "":
                        pd = CaseDic['Customer_Symptom'][:wbx_max_chr]
                    elif len(CaseDic['Problem_Description']) > wbx_max_chr:
                        pd = "(_showing truncated description_)\n\n" + CaseDic['Problem_Description'][:wbx_max_chr] + "......"
                    else:
                        pd = CaseDic['Problem_Description']
                    if len(CaseDic['Current_Status']) > wbx_max_chr:
                        cs = "(_showing truncated description_)\n\n" +  CaseDic['Current_Status'][:wbx_max_chr] + "..."
                    else:
                        cs = CaseDic['Current_Status']
                    if len(CaseDic['KT_Action_Plan']) > wbx_max_chr:
                        ap = "(_showing truncated description_)\n\n" +  CaseDic['KT_Action_Plan'][:wbx_max_chr] + "..."
                    else:
                        ap = CaseDic['KT_Action_Plan']
                    CARD_CONTENT = card.CreateCard(CaseDic['Severity'], case, CaseDic['Queue'], InQueueMinutes, CustomerDic[CaseDic['PortfolioID']]['AccountName'], CustomerDic[CaseDic['PortfolioID']]['EportalID'], CaseDic['Tech'], CaseDic['SubTech'], CaseDic['Title'], pd, cs, ap)
                    webexteams_msgs.append({"stripe" : case_stripe, "webexteams_markdown" : markdown, "CARD_CONTENT" : CARD_CONTENT})
                    CaseProcessedState[case] = True
                else:
                    webexteams_msgs.append({"stripe" : case_stripe, "webexteams_markdown" : markdown})
            
            if InQueueMinutes >= int(config['Case']['InQueue_TimeOut_Delete_Minute']):
                isSentToSydneyHTTS = False
                logger_string = logger_string+"Deleting {} Case {} from RedisDB as it's more than {} minutes.\n".format(CustomerDic[CaseDic['PortfolioID']]['AccountName'],case,\
                    config['Case']['InQueue_TimeOut_Delete_Minute'])           
                try:
                    case_stripe = CommonLib.Tech_Stripe(CaseDic['Tech'],CaseDic['SubTech'],CaseDic['Title'],CaseDic['ProductFamily'])
                except Exception as e:
                    print(e, CaseDic)
                    pass

                markdown = "**Deleting** Case [{} {}](http://mwz.cisco.com/{}) from RedisDB as it's more than {} minutes....  \n".format(CustomerDic[CaseDic['PortfolioID']]['AccountName'],case,case,config['Case']['InQueue_TimeOut_Delete_Minute'])

                webexteams_msgs.append({"stripe" : case_stripe, "webexteams_markdown" : markdown})
                del CaseProcessedState[case]
                Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())
                Redis_DB.delete(case)
    
    #log info save to log file
    if logger_string:
        logger.info(logger_string)
        
    #If there is any thing needed to send to webex team
    if len(webexteams_msgs) > 0:
        for msg_dic in webexteams_msgs:
            logger.info("ToWebex HTTS Bot Deubgging Room {}".format(msg_dic['webexteams_markdown']))
            try:
                if "CARD_CONTENT" in msg_dic:
                    webexteamsapi_htts.messages.create(roomId=config['WebexTeams']['roomid_htts_debug'], markdown=msg_dic['webexteams_markdown'], attachments=[{"contentType": "application/vnd.microsoft.card.adaptive","content": msg_dic['CARD_CONTENT']}])
                else:
                    webexteamsapi_htts.messages.create(roomId=config['WebexTeams']['roomid_htts_debug'], markdown=msg_dic['webexteams_markdown'])
            except:
                pass
            if isSentToSydneyHTTS:
                logger.info("ToWebex HTTS Sydney case alert Stripes Room {}".format(msg_dic['webexteams_markdown']))
                #try:
                #    webexteamsapi_htts.messages.create(roomId=config['WebexTeams']['roomid_htts_sydney'], markdown=msg_dic['webexteams_markdown'])
                #except:
                #    continue             
                try:
                    if "CARD_CONTENT" in msg_dic:
                        webexteamsapi_htts.messages.create(roomId=WbxRoomDic[msg_dic['stripe']]['Room ID'], markdown=msg_dic['webexteams_markdown'], attachments=[{"contentType": "application/vnd.microsoft.card.adaptive","content": msg_dic['CARD_CONTENT']}])
                    else:
                        webexteamsapi_htts.messages.create(roomId=WbxRoomDic[msg_dic['stripe']]['Room ID'], markdown=msg_dic['webexteams_markdown'])
                except:
                    pass
            if isSentToCBATeam:
                logger.info("To CBA Case alert Room {}".format(msg_dic['webexteams_markdown']))
                try:
                    if "CARD_CONTENT" in msg_dic:
                        webexteamsapi_htts.messages.create(toPersonEmail='jackylee@cisco.com', markdown=msg_dic['webexteams_markdown'], attachments=[{"contentType": "application/vnd.microsoft.card.adaptive","content": msg_dic['CARD_CONTENT']}])
                    else:
                        webexteamsapi_htts.messages.create(toPersonEmail='jackylee@cisco.com', markdown=msg_dic['webexteams_markdown'])
                except:
                    pass

    time.sleep(PollingTime)
