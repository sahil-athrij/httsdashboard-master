import pika , redis , re, configparser
import CommonLib
import PostgresqlLib 
import traceback
from flask_mongo import mongo_models

#Reading current config from file
config = configparser.ConfigParser()
config.read('config.ini')

#Initialization logger
logger_file = "RabbitMQ_HTTS_Event.log"
logger = CommonLib.HTTSLogger(name=__file__,logfile=logger_file,logfilepath=config['Logging']['LoggingPath'])

#Redis Initialization
Redis_HTTS_Pool = redis.ConnectionPool(host=config['Redis']['ServerIP'], port=config['Redis']['ServerPort'],db=config['Redis']['HTTSDB'])
Redis_HTTS = redis.StrictRedis(connection_pool=Redis_HTTS_Pool)
Redis_TAC_Pool = redis.ConnectionPool(host=config['Redis']['ServerIP'], port=config['Redis']['ServerPort'],db=config['Redis']['TACDB'])
Redis_TAC = redis.StrictRedis(connection_pool=Redis_TAC_Pool)
Redis_DB = Redis_HTTS

Redis_Send_Case_Status = ['Accepted','Case_InQueue','Dispatched_Out']

print("================================")
print("RabbitMQ HTTS Event Handler -- Receiving Event from BORG CMGW")
print("1. Send to Redis for realtime notification")
print("2. Send to PostgreSQL -- to be done")
print("Management Portal: 10.67.82.105:15672 admin cisco!123")
print("Logging: container:{} host:{} file:{}".format(config['Logging']['LoggingPath'],'/HTTSDashboard/logs',logger_file))
print("RabbitMQ IP {} Port {} Queue {} User/Pass {} {}".format(config['RabbitMQ']['serverip'],config['RabbitMQ']['serverport'],\
    config['RabbitMQ']['HTTSQueue'],config['RabbitMQ']['username'],config['RabbitMQ']['password'],))
print("Redis IP {} Port {} DB {}".format(config['Redis']['ServerIP'],config['Redis']['ServerPort'],config['Redis']['HTTSDB']))
print("================================")

pgDB = PostgresqlLib.PGSQLdb(config)
mgDB = mongo_models.HTTSMongo(config)

def EventToRedis(CaseDic,Redis_DB,logger):

    #logger.info("Processing EventToRedis....")
    #Define which evnt will send to the Redis DB
    
    try:
        if any(status in CaseDic['Case_Status'] for status in Redis_Send_Case_Status):
            
            #Create new key for Case_Inqueue and Case_Accept Time.
            if 'Case_InQueue' in CaseDic['Case_Status']:
                CaseDic['Case_InQueue_Time'] =  CaseDic['ModDateUTC']
                logger.info("MQToRedis:{} {} {} {} {} at {}".format(CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                    CaseDic['Queue'],CaseDic['Title'],CaseDic['Case_InQueue_Time']))

                pgDB.insertHTTSRecord(CaseDic)
                if 'Case_InQueue_Leaked_AH' in CaseDic['Case_Status']:
                    pgDB.insertAHRecord(CaseDic)
                    mgDB.updateAHRecord(CaseDic)

            elif 'Accepted' in CaseDic['Case_Status']:
                
                #30rd Jan 2020, the workgroup_change sometimes can not present if the case is assigned or yanked.
                # Use Status_Change New/Requeue->CEPending as 2nd ways of accepting case event.
                # Normal case may have 2 events, workgroup_change take advantage of status change as accept event.
                # Pending(No Need Now): Introduce 2 new keys Case_Acceptd_By to indicate by workgroup_change or status_change
                
                #3rd Feb 2020, if the InQueue event comes in RabbitMQ after Accept Event, the Case_Status will change to InQueue
                #though it has been accepted already.
                # Need to save the field from Accept Event for Owner and Change Case_Status to Accepted
                # Logic is:
                # Accept event save the owner and workgroup to Case_Accepted_Owner and Case_Accepted_Workgroup new items in CaseDic
                # If (In Redis) there is Case_Accepted_Time item, overwrite the Case_Status to "Accepted"
                CaseDic['Case_Accepted_Owner'] = CaseDic['Owner']
                CaseDic['Case_Accepted_Workgroup'] = CaseDic['WorkGroup']
                CaseDic['Case_Accepted_Time'] =  CaseDic['ModDateUTC']
     
                if CaseDic['Owner'] == "NULL":
                    logger.warning("Exception:{} {} {} {} {} by {} at {}".format(\
                        CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                        CaseDic['Queue'],CaseDic['Title'],CaseDic['Owner'],CaseDic['Case_Accepted_Time']))
                    return
                else:
                    logger.info("MQToRedis:{} {} {} {} {} by {} at {}".format(\
                        CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                        CaseDic['Queue'],CaseDic['Title'],CaseDic['Owner'],CaseDic['Case_Accepted_Time']))
                try:
                    pgDB.insertHTTSRecord(CaseDic)
                    logger.info("PostgreSQL: Accepted, updating {}: {} in HTTSQueue table.".format(CaseDic['CaseNumber'], CaseDic['Title']))
                    if 'Case_Accepted_Leaked_Eng' in CaseDic['Case_Status']:
                        pgDB.insertAHRecord(CaseDic)
                        mgDB.updateAHRecord(CaseDic)
                        logger.info("PostgreSQL: Accepted, updating {}: {} in AHCases table.".format(CaseDic['CaseNumber'], CaseDic['Title']))
                    if 'Case_Accepted_On' in CaseDic['Case_Status']:
                        pgDB.deleteAHRecord(CaseDic)
                        mgDB.deleteAHRecord(CaseDic)
                        logger.info("PostgreSQL: Accepted, Deleting {}: {} from AHCases table only.".format(CaseDic['CaseNumber'], CaseDic['Title']))
                except Exception as e:
                    logger.critical("Exception:  {} for {}".format(e, CaseDic))

            elif 'Dispatched_Out' in CaseDic['Case_Status']:
                #There is some issue, need to debug.
                try:
                    dispatched_time = re.search(r"Customer Scheduled Dispatch Time:(.+)",CaseDic['NoteText']).group(1)
                    CaseDic['Case_Dispatched_Time'] =  dispatched_time
                    logger.info("MQToRedis:{} {} {} {} To {}".format(CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                        CaseDic['Title'],dispatched_time))
                except Exception as e:
                    logger.critical("Exception in Dispatched_Out: {}".format(e))
                    logger.info("Exception Dispatched:{}".format(" ".join([key+":"+value for key,value in CaseDic.items()])))                
                
            if CaseDic['Owner'] == "NULL" and 'Accepted' in CaseDic['Case_Status']:
                
                logger.warning("Exception:{} {} {} {} {} by {} at {}".format(\
                    CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                    CaseDic['Queue'],CaseDic['Title'],CaseDic['Owner'],CaseDic['ModDateUTC']))
                return
            
            else:
                
                logger.info("MQToRedis:{} {} {} {} {} by {} at {}".format(\
                    CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                    CaseDic['Queue'],CaseDic['Title'],CaseDic['Owner'],CaseDic['ModDateUTC']))
            
            #logger.info("Sending {} to Redis with below info:".format(CaseDic['CaseNumber'].strip()))
            #logger.info(" ".join([key.strip()+":"+value.strip()+" " for key, value in CaseDic.items()]))
            Redis_DB.hmset(CaseDic['CaseNumber'],CaseDic)
            
        else:
            if 'Closed' in CaseDic['Case_Status']:
                try:
                    logger.info("PostgreSQL: deleting {}: {} from HTTSQueue and AHCases table.".format(CaseDic['CaseNumber'], CaseDic['Title']))
                    pgDB.deleteHTTSRecord(CaseDic)
                    pgDB.deleteAHRecord(CaseDic)
                    mgDB.deleteAHRecord(CaseDic)
                except Exception as e:
                    logger.critical("Exception:  {} for {}".format(e, CaseDic))
            
            logger.info("MQNotToRedis:{} {} {} {} {} by {} at {}".format(CaseDic['CaseNumber'],CaseDic['Severity'],CaseDic['Case_Status'],\
                CaseDic['Queue'],CaseDic['Title'],CaseDic['Owner'],CaseDic['ModDateUTC']))

    except Exception as e:
        print(e)
        traceback.print_exc()
        logger.critical("Exception:  {} for {}".format(e, CaseDic))
        logger.critical(traceback.format_exc())

def callback(ch, method, properties, body):

    #print(" [x] Received %r" % body)
    CaseDic = {string[0].strip():string[1].strip() for string in [string.split('-~-~') for string in body.decode('utf-8').split('~-~-')[1:]]}
    
    EventToRedis(CaseDic,Redis_DB,logger)

#Connect to RabbitMQ via Pika -- RabbitMQ Consumer
Pika_credentials = pika.PlainCredentials(config['RabbitMQ']['username'],config['RabbitMQ']['password'])
Pika_connection = pika.BlockingConnection(pika.ConnectionParameters(config['RabbitMQ']['serverip'],\
    int(config['RabbitMQ']['serverport']),'/',Pika_credentials))
Pika_channel = Pika_connection.channel()
Pika_channel.queue_declare(queue=config['RabbitMQ']['HTTSQueue']) #Queue on RabbitMQ
Pika_channel.basic_consume(queue=config['RabbitMQ']['HTTSQueue'], on_message_callback=callback, auto_ack=True)
#print(' [*] Waiting for HTTS Event from RabbitMQ. To exit press CTRL+C')
Pika_channel.start_consuming()
