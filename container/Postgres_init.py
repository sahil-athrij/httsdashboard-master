import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import configparser

#Reading current config from file
config = configparser.ConfigParser()
config.read('../Apps/config.ini')

try:
    # use our connection values to establish a connection
    conn = psycopg2.connect(host=config['PostgreSQL']['host'], \
                                port=config['PostgreSQL']['port'], \
                                user=config['PostgreSQL']['user'], \
                                password=config['PostgreSQL']['password'])
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    # create a psycopg2 cursor that can execute queries
    cursor = conn.cursor()
    # create a new table with a single column called "name"
    cursor.execute("""CREATE Database """ + config['PostgreSQL']['database'] + ";")
    conn.commit() # <--- makes sure the change is shown in the database
    cursor.close()
    conn.close()
except Exception as e:
    print("Uh oh, can't connect. Invalid dbname, user or password?")
    print(e)
