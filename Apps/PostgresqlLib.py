import psycopg2
import configparser

class PGSQLdb:
    def __init__(self, config):
        self._conn = psycopg2.connect(host=config['PostgreSQL']['host'], \
                                    port=config['PostgreSQL']['port'], \
                                    dbname=config['PostgreSQL']['database'], \
                                    user=config['PostgreSQL']['user'], \
                                    password=config['PostgreSQL']['password'])
        self._cursor = self._conn.cursor()

    def exec_sql(self, sqlStrList):
        for sqlStr in sqlStrList:
            cursor._cursor.execute(sqlStr)
        self._conn.commit()
    
    def createHTTSTable(self):
        sqlStr = """CREATE TABLE IF NOT EXISTS HTTSQueue 
         (CaseNumber INT PRIMARY KEY NOT NULL,
         TITLE TEXT NOT NULL,
         Owner TEXT);"""
        self._cursor.execute(sqlStr)
        self._conn.commit()

    def insertHTTSRecord(self, record):
        sqlStr = """INSERT INTO HTTSQueue 
                    (CaseNumber, Title, Owner) 
                    VALUES 
                     (%s, %s, %s) 
                    ON CONFLICT (CaseNumber) DO UPDATE
                     set Title=excluded.Title,
                         Owner=excluded.Owner;"""
        self._cursor.execute(sqlStr, (record['CaseNumber'], record['Title'], record['Owner'],))
        self._conn.commit()
    
    def deleteHTTSRecord(self, record):
        sqlStr = """DELETE FROM HTTSQueue WHERE CaseNumber=(%s);"""
        self._cursor.execute(sqlStr, (record['CaseNumber'],))
        self._conn.commit()
    
    def getHTTSRecords(self):
        sqlStr = """SELECT * FROM HTTSQueue"""
        self._cursor.execute(sqlStr)
        rows = self._cursor.fetchall()
        return rows

    def insertAHRecord(self, record):
        sqlStr = """INSERT INTO AHCases
                    (CaseNumber, Title, Owner)
                    VALUES 
                     (%s, %s, %s) 
                    ON CONFLICT (CaseNumber) DO UPDATE
                     set Title=excluded.Title,
                         Owner=excluded.Owner;"""
        self._cursor.execute(sqlStr, (record['CaseNumber'], record['Title'], record['Owner'],))
        self._conn.commit()
    
    def deleteAHRecord(self, record):
        sqlStr = """DELETE FROM AHCases WHERE CaseNumber=(%s);"""
        self._cursor.execute(sqlStr, (record['CaseNumber'],))
        self._conn.commit()
    
    def getAHRecords(self):
        sqlStr = """SELECT * FROM AHCases"""
        self._cursor.execute(sqlStr)
        rows = self._cursor.fetchall()
        return rows

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    sqldb = PGSQLdb(config)
    record = {'CaseNumber': "111111",
                'Title': "AH Test case 1",
                "Owner": "zzzz"}
#    sqldb.createHTTSTable()
    sqldb.insertAHRecord(record)
    print(sqldb.getAHRecords())
