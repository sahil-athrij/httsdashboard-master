import redis , datetime, time
import CommonLib
from webexteamssdk import WebexTeamsAPI
import configparser
import re

#Reading current config from file
config = configparser.ConfigParser()
config.read('config.ini')

#Initialization logger
logger_file = "Redis_TAC_App.log"
logger = CommonLib.HTTSLogger(name=__file__,logfile=logger_file,logfilepath=config['Logging']['LoggingPath'])

#Redis Initialization
Redis_HTTS_Pool = redis.ConnectionPool(host=config['Redis']['ServerIP'], port=config['Redis']['ServerPort'],db=config['Redis']['HTTSDB'])
Redis_HTTS = redis.StrictRedis(connection_pool=Redis_HTTS_Pool)
Redis_TAC_Pool = redis.ConnectionPool(host=config['Redis']['ServerIP'], port=config['Redis']['ServerPort'],db=config['Redis']['TACDB'])
Redis_TAC = redis.StrictRedis(connection_pool=Redis_TAC_Pool)
Redis_DB = Redis_TAC

#WebexTeams Initilization
webexteamsapi_htts = WebexTeamsAPI(access_token=config['WebexTeams']['bot_token_htts'])
InQueueMinuteAlert = {
    '1':[int(min) for min in config['Case']['P1_Alert_Minute'].split(',')],
    '2':[int(min) for min in config['Case']['P2_Alert_Minute'].split(',')],
    '3':[int(min) for min in config['Case']['P3_Alert_Minute'].split(',')],
    '4':[int(min) for min in config['Case']['P4_Alert_Minute'].split(',')],
}

#CSOne GCI Authentication/Cookie Initialization
CSOneSession = CommonLib.CSOneSession(logger=CommonLib.HTTSLogger(name="GetGCI",logfile="GetGCI-TAC-App.log",logfilepath=config['Logging']['LoggingPath']),debug=True)

PollingTime = int(config['Redis']['PollingTime'])
not_interest_queue = ["JAPAN","KOREA","CHINA","GC-Solution"]
not_interest_workgroup = ['APT-GC-Solution','KR-ACI-DL']

print("================================")
print("Polling Time:{} seconds.".format(PollingTime))
print("Redis IP {} Port {} DB {}".format(config['Redis']['ServerIP'],config['Redis']['ServerPort'],config['Redis']['TACDB']))
print("Logging: container:{} host:{} file:{}".format(config['Logging']['LoggingPath'],'/HTTSDashboard/logs',logger_file))
for severity,minutes in InQueueMinuteAlert.items():
    print("P{} InQueue Alert to WebexTeams at {} minute".format(severity," ".join([str(min) for min in minutes])))
print("================================")

while True:
    
    logger_string = ""
    webexteams_markdown = ""
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

    for eventno, case in enumerate(all_cases):
        
        CaseDic = Redis_DB.hgetall(case) #in binary format
        try:
            CaseDic = { y.decode('utf-8'): CaseDic.get(y).decode('utf-8') for y in CaseDic.keys() } #Converting to String Dictionary
        except Exception as e:
            print(e, CaseDic)
            pass
        
        #logger.info("Reading {} from Redis with below info:".format(case))
        #logger.info(" ".join([key.decode().rstrip()+":"+value.decode().rstrip()+" " for key, value in CaseDic.items()]))
        
        isInQueue = False
        isAccepted = False
        isDispatched = False
        isCancelled = False
        
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
        if 'FTS_UC_Cancelled_Time' in CaseDic.keys():
            case_status_dic[case].append("Cancelled")
            case_status_dic[case].append(str(eventno))
            isCancelled = True
            
        #If the case is not InQueue/Accept/Dispatched/Cancelled then delete
        #Sometimes only GCI exists which is wrong.
        if not isInQueue and not isAccepted and not isDispatched and not isCancelled:
            logger_string = logger_string+"1:Exception: Deleting Case {} from RedisDB in 1st iteration\n".format(case)
            logger_string = logger_string + " ".join([key.rstrip()+":"+value.rstrip()+" " for key, value in CaseDic.items()])
            logger_string = logger_string + "\n"
            skip_case.append(case)
            continue
        
        if 'Queue' in CaseDic.keys() and any(queue in CaseDic['Queue'] for queue in not_interest_queue):
            logger_string = logger_string+"1:Adding to skip Case {} for queue {}\n".format(case,CaseDic['Queue'])
            skip_case.append(case)
            
        if 'WorkGroup' in CaseDic.keys() and any(workgroup in CaseDic['WorkGroup'] for workgroup in not_interest_queue):
            logger_string = logger_string+"1:Adding to skip Case {} for workgroup {}\n".format(case,CaseDic['WorkGroup'])
            skip_case.append(case)
        
        if case not in skip_case and 'Customer_Symptom' not in CaseDic.keys():
            logger_string = logger_string+"1:Adding GCI for {}".format(case)
            Redis_TAC.hmset(case,CSOneSession.CSOneGetGCI(case))
        
    for case,status in case_status_dic.items():
        
        if case in skip_case:
            logger_string = logger_string+"2:Deleting Case {}".format(case)
            Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())
            Redis_DB.delete(case)
            continue
            
        #Dispatched need to be the first one as InQueue/Dispatched may exist for same case without taking the ownership
        #If the case is taken then dispatched, there is no issue.
        
        logger_string=logger_string+"Processing {} - {}\n".format(case," ".join(status))
        CaseDic = Redis_DB.hgetall(case)
        try:
            CaseDic = { y.decode('utf-8'): CaseDic.get(y).decode('utf-8') for y in CaseDic.keys() } #Converting to String Dictionary
        except Exception as e:
            print(e, CaseDic)
            pass
        
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
            
        ######All Case logic as below:######
        
        ###### Dispatched Case ######
        if 'Dispatched' in case_status_dic[case]:
            logger_string = logger_string+"Deleting Case {} from RedisDB as it's dispatched...".format(case)
            webexteams_markdown=webexteams_markdown+("[{}](http://mwz.cisco.com/{}) P{} {} is **dispatched** to {}  \n".format(case,case,\
                CaseDic['Severity'],CaseDic['Title'],CaseDic['Case_Dispatched_Time']))
            Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())
        
        ###### Inqueue and Accepted case ######
        elif 'InQueue' in case_status_dic[case] and 'Accepted' in case_status_dic[case]:
                        
            #FTS/UC use alias for case taker, Requeu use Owner for case taker.
            ActualCaseTaker = ""
            if CaseDic['Case_Status'] == 'Case_Accepted':
                ActualCaseTaker = CaseDic['Case_Accepted_Owner']
            elif CaseDic['Case_Status'] == 'FTS_Accepted':
                ActualCaseTaker = CaseDic['FTS_Accepted_Owner']
            elif CaseDic['Case_Status'] == 'UC_Accepted':
                ActualCaseTaker = CaseDic['UC_Accepted_Owner']
                
            logger_string = logger_string+"{} {}m {}m [{}](http://mwz.cisco.com/{}) P{} {} taken by {} {} at {}\n".format(\
                CaseDic['Case_Status'],AcceptMinutes,AcceptMinutesTillNow,case,case,CaseDic['Severity'],\
                CaseDic['Title'],ActualCaseTaker,CaseDic['WorkGroup'],CaseDic['Case_Accepted_Time'])

            if AcceptMinutesTillNow >= int(config['Case']['Delayed_Process_Minute']):

                webexteams_markdown=webexteams_markdown+"**{}** {}m {}m [{}](http://mwz.cisco.com/{}) P{} {} taken by {} {} at {}  \n".format(CaseDic['Case_Status'],AcceptMinutes,AcceptMinutesTillNow,case,case,CaseDic['Severity'],\
                    CaseDic['Title'],ActualCaseTaker,CaseDic['WorkGroup'],CaseDic['Case_Accepted_Time'])
                
                logger_string = logger_string+"Deleting Case {} from RedisDB as it's accepted.".format(case)
                Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())  
                Redis_DB.delete(case)
                
        ###### Cancelled Case ######
        elif 'Cancelled' in case_status_dic[case] : #remove --- 'InQueue' in case_status_dic[case] and 
            
            logger_string = logger_string+"{} {}mins [{}](http://mwz.cisco.com/{}) P{} {} at {}\n".format(\
                CaseDic['Case_Status'],InQueueMinutes,case,case,CaseDic['Severity'],CaseDic['Title'],CaseDic['Queue'],\
                CaseDic['FTS_UC_Cancelled_Time'])    
            logger_string = logger_string+"Deleting Case {} from RedisDB as it is FTS_UC_Cancelled.".format(case) 
                
            webexteams_markdown = webexteams_markdown+"**{}** {}mins [{}](http://mwz.cisco.com/{}) P{} {} {} at {}  \n".format(\
                CaseDic['Case_Status'],InQueueMinutes,case,case,CaseDic['Severity'],CaseDic['Title'],CaseDic['Queue'],\
                CaseDic['FTS_UC_Cancelled_Time'])
            
            Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())
            Redis_DB.delete(case)
            
        ###### Accepted without InQueue case #######
        elif 'InQueue' not in case_status_dic[case] and 'Accepted' in case_status_dic[case]:
                
            logger_string = logger_string+"Exception {}mins [{}](http://mwz.cisco.com/{}) P{} {} {} is AcptNoInQueue time.\n".format(AcceptMinutesTillNow,case,case,CaseDic['Severity'],CaseDic['Title'],CaseDic['Queue'])

            #2019-12-31 11:20:44,799 88169348 4 Case_Accepted at 2019-12-31 11:20:22
            #2019-12-31 11:20:56,989 688169348 4 Case_InQueue at 2019-12-31 11:19:38
            #2019-12-31 11:20:54,034-INFO-There are 1 events in RedisDB 688169348
            #Asperabove, there is a situation Accepted event prior to InQueue event, while Redis read between them.
            #Add logic only Accepted more than 2 minutes , then deleted the event -- wait for InQueue event.
            
            #2nd Scneario is FTS_UC_Accetped and Case_Accepted will not have FTS_InQueue/UC_Inqueue entry which is expected.
            
            if AcceptMinutesTillNow > int(config['Case']['Delayed_Process_Minute']) or AcceptMinutesTillNow == -1:
                logger_string = logger_string+"Deleting {} {} after {}mins in RedisDB as AcptNoInQueue...".format(\
                    case,CaseDic['Title'],AcceptMinutesTillNow)
                webexteams_markdown = webexteams_markdown+"{}mins [{}](http://mwz.cisco.com/{}) P{} {} {} **AcptNoInQueue** time  \n".format(AcceptMinutesTillNow,case,case,CaseDic['Severity'],CaseDic['Title'],CaseDic['Queue'])
                if Redis_DB.hgetall(case).keys():
                    Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())
                    Redis_DB.delete(case)
                else:
                    logger_string = logger_string+"Error deleting {} {}\n".format(case,CaseDic['Title'])
        
        ###### Inqueue Case without taken ######
        elif 'InQueue' in case_status_dic[case] and 'Accepted' not in case_status_dic[case]:

            logger_string = logger_string+"{} {}mins [{}](http://mwz.cisco.com/{}) P{} {} InQueue {} at {}\n".format(\
                CaseDic['Case_Status'],InQueueMinutes,case,case,CaseDic['Severity'],CaseDic['Title'],CaseDic['Queue'],\
                CaseDic['Case_InQueue_Time'])
            
            if CaseDic['Severity'] != '-1' and InQueueMinutes in InQueueMinuteAlert[CaseDic['Severity']]:
                logger_string = logger_string+"ToWebex P{} {} in queue for {} mins.\n".format(CaseDic['Severity'],case, InQueueMinutes)
                webexteams_markdown = webexteams_markdown+"**{}** {}mins [{}](http://mwz.cisco.com/{}) P{} {} {} at {}  \n".format(\
                    CaseDic['Case_Status'],InQueueMinutes,case,case,CaseDic['Severity'],CaseDic['Title'],CaseDic['Queue'],\
                    CaseDic['Case_InQueue_Time'])
            
            if InQueueMinutes >= int(config['Case']['InQueue_TimeOut_Delete_Minute']):
                logger_string = logger_string+"Deleting Case {} from RedisDB as it's more than {} minutes.".format(case,\
                    config['Case']['InQueue_TimeOut_Delete_Minute'])           
                webexteams_markdown = webexteams_markdown+"**Deleting** Case [{}](http://mwz.cisco.com/{}) from RedisDB existing {} minutes....  \n".format(case,case,config['Case']['InQueue_TimeOut_Delete_Minute'])
                Redis_DB.hdel(case,*Redis_DB.hgetall(case).keys())
                Redis_DB.delete(case)
                
    if logger_string:
        logger.info(logger_string)
        
    if webexteams_markdown:
        logger.info("ToWebex {}".format(webexteams_markdown.strip()))
        try:
            pass
            #webexteamsapi_htts.messages.create(toPersonEmail='zdazhi@cisco.com', markdown=webexteams_markdown)
        except:
            pass
            
    time.sleep(PollingTime)
