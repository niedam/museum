import psycopg2
from dbinfo import *

# Init database connection.
try:
    conn = psycopg2.connect(host=host, user=user, password=password, dbname=dbname)
    conn.set_client_encoding('UTF8')
except psycopg2.Error:
    exit(-1)


# Change empty string to `None`.
def check_none(atr):
    if '' == atr:
        return None
    return atr


# Return two list:
#  -> artists without exhibits in database
#  -> artists whose exhibits aren't exhibited in any gallery
def notification():
    cur = conn.cursor()
    cur.execute("SELECT * FROM no_exhibits")
    no_exhibits = cur.fetchall()
    cur.execute("SELECT * FROM no_exhibited")
    no_exhibited = cur.fetchall()
    return no_exhibits, no_exhibited
