from random import *
from datetime import *
import psycopg2
from psycopg2 import sql
from dbinfo import *

try:
    conn = psycopg2.connect(host = host, user = user, password = password, dbname = dbname)
    conn.set_client_encoding('UTF8')
except:
    exit(-1)

cur = conn.cursor()


print('6')

def gener(ex, start, end):
    result = []
    day = timedelta(days=1)
    s = start + day * randint(0,31)
    e = s
    cur.execute(sql.SQL("SELECT rentable FROM exhibits WHERE id = %s"), [ex])
    rentable = cur.fetchone()[0]
    while s < end:
        if rentable:
            if randint(0, 2) == 0: # Exhibited
                time = randint(0, 100)
                e = s + (time * day)
                result += [[ex, s, e, randint(1,13), None]]
                s = e + (randint(1, 30) * day)
            else: #Rented
                time = randint(0, 29)
                e = s + (time * day)
                result += [[ex, s, e, None, randint(1,7)]]
                s = e + (randint(1, 45) * day)
        else: #Exhibited
            time = randint(0, 180)
            e = s + (time * day)
            result += [[ex, s, e, randint(1, 13), None]]
            s = e + (randint(1, 30) * day)
    return result




data = []
for i in range(1, 87):
    data += gener(i, datetime(year=2018,month=1,day=1), datetime(year=2020,month=5,day=1))



cur.executemany(sql.SQL("INSERT INTO exhibits_history (exhibit, since_date, to_date, exhibited_in, rented_to) VALUES (%s, %s, %s, %s, %s)"), data)

print("exec")
conn.commit()
print("commit")