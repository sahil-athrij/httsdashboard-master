import pika , redis, re , configparser
import CommonLib

#Reading current config from file
config = configparser.ConfigParser()
config.read('config.ini')

#Initialization logger
default_logger_file = 'RabbitMQ_TAC_Event.log'
default_logger = CommonLib.HTTSLogger(name=default_logger_file,logfile=default_logger_file,logfilepath=config['Logging']['LoggingPath'])

aci_logger_file = "RabbitMQ_ACI_Event.log"
aci_logger = CommonLib.HTTSLogger(name=aci_logger_file,logfile=aci_logger_file,logfilepath=config['Logging']['LoggingPath'])

collab_logger_file = "RabbitMQ_COLLAB_Event.log"
collab_logger = CommonLib.HTTSLogger(name=collab_logger_file,logfile=collab_logger_file,logfilepath=config['Logging']['LoggingPath'])

dcrs_logger_file = "RabbitMQ_DCRS_Event.log"
dcrs_logger = CommonLib.HTTSLogger(name=dcrs_logger_file,logfile=dcrs_logger_file,logfilepath=config['Logging']['LoggingPath'])

ent_logger_file = "RabbitMQ_ENT_Event.log"
ent_logger = CommonLib.HTTSLogger(name=ent_logger_file,logfile=ent_logger_file,logfilepath=config['Logging']['LoggingPath'])

sec_logger_file = "RabbitMQ_SEC_Event.log"
sec_logger = CommonLib.HTTSLogger(name=sec_logger_file,logfile=sec_logger_file,logfilepath=config['Logging']['LoggingPath'])

sp_logger_file = "RabbitMQ_SP_Event.log"
sp_logger = CommonLib.HTTSLogger(name=sp_logger_file,logfile=sp_logger_file,logfilepath=config['Logging']['LoggingPath'])

sv_logger_file = "RabbitMQ_SV_Event.log"
sv_logger = CommonLib.HTTSLogger(name=sv_logger_file,logfile=sv_logger_file,logfilepath=config['Logging']['LoggingPath'])

tetration_logger_file = "RabbitMQ_Tetration_Event.log"
tetration_logger = CommonLib.HTTSLogger(name=tetration_logger_file,logfile=tetration_logger_file,logfilepath=config['Logging']['LoggingPath'])

#Redis Initialization
Redis_HTTS_Pool = redis.ConnectionPool(host=config['Redis']['ServerIP'], port=config['Redis']['ServerPort'],db=config['Redis']['HTTSDB'])
Redis_HTTS = redis.StrictRedis(connection_pool=Redis_HTTS_Pool)
Redis_TAC_Pool = redis.ConnectionPool(host=config['Redis']['ServerIP'], port=config['Redis']['ServerPort'],db=config['Redis']['TACDB'])
Redis_TAC = redis.StrictRedis(connection_pool=Redis_TAC_Pool)
Redis_DB = Redis_TAC

Redis_Send_Case_Status = ['Accepted','InQueue','Dispatched_Out','FTS_UC_Cancelled','UC_Closed']

print("================================")
print("RabbitMQ TAC Event Handler -- Receiving Event from BORG CMGW")
print("1. Send to Redis for realtime notification")
print("2. Send to PostgreSQL -- to be done")
print("Management Portal: 10.67.82.105:15672 admin cisco!123")
#print("Logging: container:{} host:{} file:{}".format(config['Logging']['LoggingPath'],'/HTTSDashboard/logs',logger_file))
print("RabbitMQ IP {} Port {} Queue {} User/Pass {} {}".format(config['RabbitMQ']['serverip'],config['RabbitMQ']['serverport'],\
    config['RabbitMQ']['TACQueue'],config['RabbitMQ']['username'],config['RabbitMQ']['password'],))
print("Redis IP {} Port {} DB {}".format(config['Redis']['ServerIP'],config['Redis']['ServerPort'],config['Redis']['TACDB']))
print("================================")

def callback(ch, method, properties, body):
    
    isSentToRedis = False
    
    #print(" [x] Received %r" % body)
    try:
        CaseDic = {string[0].strip():string[1].strip() for string in [string.split('-~-~') for string in body.decode('utf-8').split('~-~-')[1:]]}
    except IndexError as e:
        print("Index error {}".format(e))
        print(body.decode('utf-8'))
        return

    #print(CaseDic)
    if CaseDic['RabbitMQTech'] == 'ACI' or CaseDic['RabbitMQTech'] == 'ACI_FTS_UC':
        logger = aci_logger
        isSentToRedis = True
    elif CaseDic['RabbitMQTech'] == 'COLLAB' or CaseDic['RabbitMQTech'] == 'COLLAB_FTS_UC':
        logger = collab_logger
    elif CaseDic['RabbitMQTech'] == 'DCRS' or CaseDic['RabbitMQTech'] == 'DCRS_FTS_UC':
        logger = dcrs_logger
    elif CaseDic['RabbitMQTech'] == 'ENT' or CaseDic['RabbitMQTech'] == 'ENT_FTS_UC':
        logger = ent_logger
    elif CaseDic['RabbitMQTech'] == 'SEC' or CaseDic['RabbitMQTech'] == 'SEC_FTS_UC':
        logger = sec_logger
    elif CaseDic['RabbitMQTech'] == 'SP' or CaseDic['RabbitMQTech'] == 'SP_FTS_UC':
        logger = sp_logger
    elif CaseDic['RabbitMQTech'] == 'SV' or CaseDic['RabbitMQTech'] == 'SV_FTS_UC':
        logger = sv_logger
    elif CaseDic['RabbitMQTech'] == 'TETRATION' or CaseDic['RabbitMQTech'] == 'TETRATION_FTS_UC':
        logger = tetration_logger
        isSentToRedis = True
    else:
        logger = default_logger
        
    #Define which evnt will send to the Redis DB
    if any(status in CaseDic['Case_Status'] for status in Redis_Send_Case_Status):
        
        
        #Create new key for Case_Inqueue and Case_Accept Time.
        if 'InQueue' in CaseDic['Case_Status']:
            
            CaseDic['Case_InQueue_Time'] =  CaseDic['ModDateUTC']
            logger.info("MQToRedis:{} {} {} {} {} at {}".format(CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                CaseDic['Queue'],CaseDic['Title'],CaseDic['Case_InQueue_Time']))

        elif 'Accepted' in CaseDic['Case_Status'] or 'UC_Closed' in CaseDic['Case_Status']:
            ActualCaseTakeTime = ""
            if CaseDic['Case_Status'] == "Case_Accepted":
                CaseDic['Case_Accepted_Owner'] = CaseDic['Owner']
                CaseDic['Case_Accepted_Workgroup'] = CaseDic['WorkGroup']
                CaseDic['Case_Accepted_Time'] =  CaseDic['ModDateUTC']
                ActualCaseTakeTime = CaseDic['ModDateUTC']
            elif CaseDic['Case_Status'] == "FTS_Accepted":
                CaseDic['FTS_Accepted_Owner'] = CaseDic['Alias']
                CaseDic['FTS_Accepted_Time']=  CaseDic['ModDateUTC']
                CaseDic['WorkGroup'] = 'FTS_WORKGROUP'
                ActualCaseTakeTime = CaseDic['ModDateUTC'] 
            elif CaseDic['Case_Status'] == "UC_Accepted" or CaseDic['Case_Status'] == "UC_Closed":
                CaseDic['UC_Accepted_Owner'] = CaseDic['Alias']
                CaseDic['UC_Accepted_Time']=  CaseDic['ModDateUTC']
                CaseDic['WorkGroup'] = 'UC_WORKGROUP'
                ActualCaseTakeTime  = CaseDic['ModDateUTC']
            ActualCaseTaker = CaseDic['Owner']

            if CaseDic['Case_Status'] == "FTS_Accepted" or CaseDic['Case_Status'] == "UC_Accepted" or CaseDic['Case_Status'] == "UC_Closed":
                ActualCaseTaker = CaseDic['Alias']
                
            if CaseDic['Owner'] == "NULL":
                logger.warning("Exception:{} {} {} {} by {} {} at {}".format(\
                    CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                    CaseDic['Title'],ActualCaseTaker,CaseDic['WorkGroup'],ActualCaseTakeTime))
                return
            else:
                logger.info("MQToRedis:{} {} {} {} taken by {} {} at {}".format(\
                    CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                    CaseDic['Title'],ActualCaseTaker,CaseDic['WorkGroup'],ActualCaseTakeTime))
        
        elif 'FTS_UC_Cancelled' in CaseDic['Case_Status']:
            
            CaseDic['FTS_UC_Cancelled_Time'] =  CaseDic['ModDateUTC']
            logger.info("MQToRedis:{} {} {} {} {} by {} {} at {}".format(\
                CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                CaseDic['Queue'],CaseDic['Title'],CaseDic['Owner'],CaseDic['WorkGroup'],CaseDic['FTS_UC_Cancelled_Time']))
                
        elif 'Dispatched_Out' in CaseDic['Case_Status']:
            
            dispatched_time = re.search(r"Customer Scheduled Dispatch Time:(.+)",CaseDic['NoteText']).group(1)
            CaseDic['Case_Dispatched_Time'] =  dispatched_time
            logger.info("MQToRedis:{} {} {} {} To {}".format(CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                CaseDic['Title'],dispatched_time))
        
        #logger.info("Sending {} to Redis with below info:".format(CaseDic['CaseNumber'].strip()))
        #logger.info(" ".join([key.strip()+":"+value.strip()+" " for key, value in CaseDic.items()]))
        if isSentToRedis:
            Redis_DB.hmset(CaseDic['CaseNumber'],CaseDic)
        
    else:
        if CaseDic['Case_Status'] == 'Case_Closed':
            logger.info("MQ:{} {} {} {} by {} {} at {}".format(CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                CaseDic['Title'],CaseDic['Owner'],CaseDic['WorkGroup'],CaseDic['ModDateUTC']))            
        else:
            logger.info("MQ:{} {} {} {} {} by {} {} at {}".format(CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                CaseDic['Queue'],CaseDic['Title'],CaseDic['Owner'],CaseDic['WorkGroup'],CaseDic['ModDateUTC']))

#Connect to RabbitMQ via Pika
Pika_credentials = pika.PlainCredentials(config['RabbitMQ']['username'],config['RabbitMQ']['password'])
Pika_connection = pika.BlockingConnection(pika.ConnectionParameters(config['RabbitMQ']['serverip'],\
    int(config['RabbitMQ']['serverport']),'/',Pika_credentials))
Pika_channel = Pika_connection.channel()
Pika_channel.queue_declare(queue=config['RabbitMQ']['TACQueue']) #Queue on RabbitMQ
Pika_channel.basic_consume(queue=config['RabbitMQ']['TACQueue'], on_message_callback=callback, auto_ack=True)
#print(' [*] Waiting for TAC Event from RabbitMQ. To exit press CTRL+C')
Pika_channel.start_consuming()
