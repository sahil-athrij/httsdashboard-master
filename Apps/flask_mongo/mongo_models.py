import pymongo
import configparser

class HTTSMongo:
    def __init__(self, config):
        self.mClient = pymongo.MongoClient(host=config['MongoDB']['host'],
                                           port=int(config['MongoDB']['port']),
                                           username=config['MongoDB']['user'],
                                           password=config['MongoDB']['password'])
        self.mDB = self.mClient[config['MongoDB']['database']]
        self.httsAHCol = self.mDB['HTTSQueue']
        self.httsAHCol.create_index([("CaseNumber", pymongo.ASCENDING)], unique=True)

    def updateAHRecord(self, record):
        srFilter = {'CaseNumber': record['CaseNumber']}
        return self.httsAHCol.update_one(srFilter, {"$set": record}, upsert=True)

    def deleteAHRecord(self, record):
        srFilter = {'CaseNumber': record['CaseNumber']}
        return self.httsAHCol.delete_many(srFilter)

    def getAHRecords(self):
        def convert(x):
            x.pop('_id')
            return x
        return [ convert(x) for x in self.httsAHCol.find()]


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('../config.ini')
    httsmg = HTTSMongo(config)
    record = {"Case_Status":"Case_Accepted_Leaked_Eng",
      "Subject": "Stealhead down - EXSi need new firmware  SubTech:Unified Computing System (UCS E-Series Server Modules)", 
      "CaseNumber": "688319230"}
#    sqldb.createHTTSTable()
    httsmg.deleteAHRecord({'CaseNumber': "688319230"})
    httsmg.updateAHRecord(record)
    print(httsmg.getAHRecords())
