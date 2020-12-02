import datetime
import logging
import logging.handlers
import configparser
import csv
import requests
from requests.auth import HTTPBasicAuth
import json
import re

#Reading current config from file
config = configparser.ConfigParser()
config.read('config.ini')

def isOnShift(local_timezone,event_time_utc_str):
    
    '''
    Summer time onshift means 12:00 - 18:00 in weekdays, and winter time onshift means 10:00 - 16:00 in weekdays, currently public holiday is not caculated
    isoweekday() Return the day of the week as an integer, where Monday is 1 and Sunday is 7. For example, date(2002, 12, 4).isoweekday() == 3, a Wednesday. 
    '''
    
    '''
    Usage of the local timezone
    import pytz
    from pytz import timezone
    local_timezone = timezone('Australia/Sydney')
    '''
    
    shift_start_hour = int(config['Case']['Shift_start_hour'])
    shift_start_minute = int(config['Case']['Shift_start_min'])
    shift_period = int(config['Case']['Shift_period'])
    shift_start_time_dt = datetime.time (hour=shift_start_hour, minute=0, tzinfo=local_timezone)
    shift_end_time_dt = datetime.time (hour=shift_start_hour+shift_period, minute=0, tzinfo=local_timezone)
    
    event_time_utc_datetime = datetime.datetime.strptime(event_time_utc_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
    event_time_local_datetime = event_time_utc_datetime.astimezone(local_timezone)
    event_time_local_date = event_time_local_datetime.date()
    event_time_local_time = event_time_local_datetime.time()
 
    #print(str(start_time) + " " + str(event_time_aest_datetime)+ " " + str(end_time))

    if (shift_start_time_dt <= event_time_local_time <= shift_end_time_dt) and (event_time_local_date.isoweekday() < 6):
        return True
    else:
        return False

class HTTSLogger(object):
    
    def __init__(self,name=__file__,formatter='-%(asctime)s-%(levelname)s-%(message)s',\
                 level=logging.DEBUG,logfile='logfile.log',logfilepath=config['Logging']['LoggingPath']):
        
        self.name = name
        self.logger_instance = logging.getLogger(self.name)
        self.logger_instance.setLevel(level)
        self.logfile = logfile
        self.logfilepath = logfilepath
        self.level = level
        
        # create console handler and set level to debug
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(self.level)
        
        # Create SizeRotateFileHandler and set level to debug 5M
        self.sizebased_file_hanlder = logging.handlers.RotatingFileHandler(self.logfilepath+self.logfile, mode='a', maxBytes=1024*1024*100, backupCount=20, encoding=None, delay=0)
        self.sizebased_file_hanlder.setLevel(self.level)
        
        # create formatter
        self.formatter = logging.Formatter(self.name+formatter)
        
        # add formatter to handler
        self.console_handler.setFormatter(self.formatter)
        self.sizebased_file_hanlder.setFormatter(self.formatter)
        
        # add handler to logger
        # self.logger_instance.addHandler(self.console_handler) #Remove the comment if STDOUT handler on screen needed
        self.logger_instance.addHandler(self.sizebased_file_hanlder)

    def critical(self,msg):
        return self.logger_instance.critical(msg)
    
    def error(self,msg):
        return self.logger_instance.error(msg)
    
    def warning(self,msg):
        return self.logger_instance.warning(msg)

    def info(self,msg):
        return self.logger_instance.info(msg)
    
    def debug(self,msg):
        return self.logger_instance.debug(msg)

def read_csv(filename, keyfield, separator):
    """
    Inputs:
      filename  - name of CustomerList CSV file
      keyfield  - field to use as key for rows
      separator - character that separates fields
    Output:
      Returns a dictionary of dictionaries where the outer dictionary
      maps the value in the PorfolioID to the corresponding row in the
      CSV file.  The inner dictionaries map the field names to the
      field values for that row.
    """
    table = {}
    with open(filename, newline='', encoding='utf-8-sig') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=separator)
        for row in csvreader:
            rowid = row[keyfield]
            table[rowid] = row
    return table


def Tech_Stripe(tech, subtech, title, productfamily):
    """
    Map tech, subtect and pdocutfamily to technology stripe
    """
    TechToStripeDic, PidSSPTtoStripeDic = {}, {}
    TechToStripeDic = read_csv(config['CSOne']['Tech_to_Stripe_Map'], "Tech", ",")
    PidSSPTtoStripeDic = read_csv(config['CSOne']['Pid_SSPT_to_Strip_Map'], "ProductFamily", ",")
    if tech == 'Hardware' or tech == 'Other':
        case_stripe_match, case_stripe = "", ""
        for pid in PidSSPTtoStripeDic:
            if re.search(pid,title,re.IGNORECASE):
                case_stripe_match = PidSSPTtoStripeDic[pid]['Stripe']
            elif re.search(pid,subtech,re.IGNORECASE):
                case_stripe_match = PidSSPTtoStripeDic[pid]['Stripe']
            elif re.search(pid,productfamily,re.IGNORECASE):
                case_stripe_match = PidSSPTtoStripeDic[pid]['Stripe']
        if not case_stripe_match == "":
            case_stripe = case_stripe_match
        else:
            case_stripe = "Other"
    elif tech == "Router and IOS-XE Architecture" or tech == "Routing Protocols (Includes NAT and HSRP)":
        case_stripe = ""
        if re.search("ASR1",title,re.IGNORECASE):
            case_stripe = "ENT"
        elif re.search("ASR",title,re.IGNORECASE):
            case_stripe = "SP"
        else:
            case_stripe = TechToStripeDic[tech]['Stripe']
    elif tech == "Solution Support (SSPT - contract required)":
        case_stripe = case_stripe = PidSSPTtoStripeDic[subtech]['Stripe']
    else:
        case_stripe = TechToStripeDic[tech]['Stripe']
    return case_stripe
    
#Logger Initialization
logger_file = "CommonLib.log"
logger = HTTSLogger(name=__file__,logfile=logger_file,logfilepath=config['Logging']['LoggingPath'])

class CSOneSession(object):
    
    def __init__(self, username="sydhtts.gen",password="@dm1nC1sc0",logger=logger,debug=False):
        
        self.username = username
        self.password = password
        self.logger = logger
        self.debug = debug
        self.isCSOneAuth, self.isAuthResp, self.AuthResp = self.CSOneAuthAPI(username,password)

    def CSOneAuthAPI(self,username,password):
        
        # Authentication by ccoid/pass
        auth_url = "https://scripts.cisco.com/api/v2/auth/login"
        isAuth = False
        isResponse = False
        response = ""
        
        try:
            response = requests.get(auth_url, auth=HTTPBasicAuth(username, password))
            #Auth result is 201 Created , if it is not 201, it could be 401 AUthoried or other
            isResponse = True
            if response.status_code == 201:
                isAuth = True
            if self.debug:
                self.logger.info("CSOneAuthAPI:CSOneAuth Result {} {}".format(response.status_code,response.reason))
        except Exception as e:
            if self.debug:
                self.logger.info("CSOneAuthAPI:CSOneAuth Failure - {}".format(e))

        return isAuth, isResponse, response


    def CSOneGetGCIAPI(self,CaseNo):
        
        isCurrentStatusFound = False
        isKTActionPlanFound = False
        ReturnGCI = {}
        isGotGCI = False
        isGotResponse = False
        response = ""
        
        #Get all fields
        base_url = "https://scripts.cisco.com/api/v2/csone";
        #all_resp = requests.get(url, cookies=cookies)
        #print(all_resp.text)
    
        #cisco_sr = "680915033"
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        data_field = ["Problem_Description__c","Customer_Symptom__c","Shadow_Notes__r"]
        #Use web developer tool to get all fileds.... or find the doc somewhere (swagger @#$$%^)
        try:
            response = requests.post("{}/{}".format(base_url,CaseNo),headers=headers, data=json.dumps(data_field),cookies=self.AuthResp.cookies)
            isGotResponse = True
            if self.debug:
                self.logger.info("CSOneGetGCIAPI:Pull CSOne Post Response - {} {}".format(response.status_code,response.reason))
        except Exception as e:
            if self.debug:
                self.logger.info("CSOneGetGCIAPI:Pull CSOne Post Failure - {}".format(e))
            
        #print("Response {} {}".format(response.status_code,response.reason))
        if isGotResponse:
            if response.status_code == 200:
                isGotGCI = True
                response_dic = json.loads(response.text)
                
                #The filed below could be None means the value does not exists while the key is still there.
                ReturnGCI['Problem_Description'] = ""
                ReturnGCI['Customer_Symptom'] = ""
                ReturnGCI["Current_Status"] = ""
                ReturnGCI["KT_Action_Plan"] = ""
                
                if 'Problem_Description__c' in response_dic.keys() and response_dic['Problem_Description__c']:
                    ReturnGCI['Problem_Description'] = response_dic['Problem_Description__c']
                if 'Customer_Symptom__c' in response_dic.keys() and response_dic['Customer_Symptom__c']:
                    CusomterSymptom = response_dic['Customer_Symptom__c'].split("Problem Details:")
                    if len(CusomterSymptom) >= 2:
                        ReturnGCI['Customer_Symptom'] = CusomterSymptom[1]
                    else:
                        ReturnGCI['Customer_Symptom'] = CusomterSymptom[0]
                        
                for key, value in enumerate(response_dic['Shadow_Notes__r']['records'][::-1]):
                    #The shadow_notes__r is a list sorted by timestamp, reading from the last note to get latest current status and KT AP
                    if value["NoteType__c"] == "CURRENT STATUS" and value['Note__c']:
                        ReturnGCI["Current_Status"] = value['Note__c']
                        isCurrentStatusFoun = True
                    if value["NoteType__c"] == "KT ACTION PLAN" and value['Note__c']:
                        ReturnGCI["KT_Action_Plan"] = value['Note__c']
                        isKTActionPlanFound = True
                    if isCurrentStatusFound and isKTActionPlanFound:
                        break
                
                if self.debug:
                    self.logger.info("CSOneGetGCIAPI Result {}".format(CaseNo))
                    self.logger.info(ReturnGCI)
            else:
                if self.debug:
                    self.logger.info("CSOneGetGCIAPI Response Failure {} {}".format(response.status_code,response.reason))
                
        return isGotGCI, isGotResponse, response, ReturnGCI
        #return json.loads(specific_resp.text)
    
    def CSOneGetGCI(self,case):
        
        # 1. If CSOneAuthe succeeds, then pull the GCI
        # 1.1 if pull GCI succeeds, continue
        # 1.2 if pull GCI failured, pop up the response status_code and reason, continue
        # 1.3 if pull GCI thwor exception, continue
        # 2. if CSOneAuth fails
        # 2.1 Go through CSOneAuth 
        # 2.2 -> 1.1
        # 2.3 -> 1.2
        # 2.4 -> 1.3
        
        GCIDic = {}
    
        if not self.isCSOneAuth:
            
            if self.debug:
                self.logger.info("CSOneGetGCI:CSOne Authentication Try....")
                
            self.isCSOneAuth, self.isAuthResp, self.AuthResp = self.CSOneAuthAPI(config['CSOne']['username'],config['CSOne']['password'])
            
            if isCSOneAuthResp:
                if self.debug:
                    self.logger.info("CSOneGetGCI:CSOne Auth Result {} {}".format(self.AuthResp.status_code,self.AuthResp.reason))
                
        if self.isCSOneAuth:
            
            if self.debug:
                self.logger.info("CSOneGetGCI:CSOne Authenticated_1 succeeds(cookie) and Continue")
            
            isGotGCI, isGotGCIResp, GetGCIRespnose, CSOneGCIDic = self.CSOneGetGCIAPI(case)
            
            if isGotGCI:
                if self.debug:
                    self.logger.info("CSOneGetGCI:GotGCI Succeed_1 and Response with {} {}".format(GetGCIRespnose.status_code,GetGCIRespnose.reason))
                for key, value in CSOneGCIDic.items():
                    GCIDic[key] = value
    
            #If the cookie timeout, response most likly is 401 Authorized/403 Forbidden
            #But in this case, any response which is not 200 will retry and refresh the cookie and do it again.
            elif not isGotGCI and isGotGCIResp:    
                
                if self.debug:
                    self.logger.info("CSOneGetGCI:GotGCI Failure_2 and Response with {} {}".format(GetGCIRespnose.status_code,GetGCIRespnose.reason))
                
                self.isCSOneAuth, self.isAuthResp, self.AuthResp = self.CSOneAuthAPI(config['CSOne']['username'],config['CSOne']['password'])
                
                if self.isCSOneAuth:
                    if self.debug:
                        self.logger.info("CSOneGetGCI:CSOne Authenticated_2 succeds and Continue")
                    isGotGCI, isGotGCIResp, GetGCIRespnose, CSOneGCIDic = self.CSOneGetGCIAPI(case)
                    if isGotGCI:
                        self.logger.info("CSOneGetGCI:GotGCI Succeed_2 and Response with {} {}".format(GetGCIRespnose.status_code,GetGCIRespnose.reason))
                        for key, value in CSOneGCIDic.items():
                            GCIDic[key] = value
            
            else:
                if self.debug:
                    self.logger.info("CSOneGetGCI:GotGCI Failure_1 and Response with {} {}".format(GetGCIRespnose.status_code,GetGCIRespnose.reason))
            
        return GCIDic
    
if __name__ == '__main__':
    logger = HTTSLogger()
    logger.critical("This is a critical test")
    logger.error("This is a error test")
    logger.warning("This is a warning test")
    logger.info("This is a info test")
    logger.debug("This is a debug test")
