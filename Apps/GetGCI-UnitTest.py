import CommonLib
import configparser
import redis
import time

#Reading current config from file
config = configparser.ConfigParser()
config.read('config.ini')

#Initialization logger
logger_file = "GetGCI-UnitTest.log"
logger = CommonLib.HTTSLogger(name=__file__,logfile=logger_file,logfilepath=config['Logging']['LoggingPath'])

#CSOne GCI Authentication/Cookie Initialization
CSOneSession = CommonLib.CSOneSession("sydhtts.gen","@dm1nC1sc0",logger,True)
if CSOneSession.isAuthResp:
    logger.info("CSOne Initial Authentication Result {} {} ".format(CSOneSession.AuthResp.status_code,CSOneSession.AuthResp.reason))

#17th Feb 2020 Adding GCI in the 1st Iteration.
#TODO: implement GetGCI in CommonLib
#Try adding CaseDic['Problem_Description'] CaseDic['Customer_Symtpom'] CaseDic['Current_Status'] CaseDic['KT_Action_Plan']
#It could be no result --- e.g. new case

#Read case from Redis
Redis_TAC_Pool = redis.ConnectionPool(host='10.67.82.105', port=6379,db=1)
Redis_TAC = redis.StrictRedis(host='10.67.82.105',port=6379,db=1)

while True:
    
    CaseList = []
    CaseList = CaseList + Redis_TAC.keys()
    CaseList = [case.decode() for case in CaseList]
    logger_string = ""
    
    #CaseList.append("688489541")
    #CaseList.append("687777638")
    
    logger_string = "GetGCI:Case List {}\n".format(" ".join(CaseList))
        
    for case in CaseList:
        #logger.info("Reading from Redis {}\n".format(case))
        CaseDic = Redis_TAC.hgetall(case)
        #logger.info(CaseDic)
        
        try:
            CaseDic = { y.decode('utf-8'): CaseDic.get(y).decode('utf-8') for y in CaseDic.keys() } #Converting to String Dictionary
        except Exception as e:
            print(e, CaseDic)
            pass
        
        if 'Customer_Symtpom' not in CaseDic.keys():
            #logger.info(CaseDic.keys())
            GCIDic = CSOneSession.CSOneGetGCI(case)
            #logger.info("New GCI Dic {}".format(case))
            #for key, value in GCIDic.items():
            #    logger.info("{}:{}".format(key,value))
            Redis_TAC.hmset(case,GCIDic)
            logger_string = logger_string + "GetGCI:Write to Redis {}\n".format(case)
            #logger.info(CaseDic)
        else:
            logger_string = logger_string+"GetGCI:Entry exists, no need to write {}\n".format(case) 
            
    if logger_string:
        logger.info(logger_string.strip())

    time.sleep(20)