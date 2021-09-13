#%%
import numpy as np
import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import requests
from contextlib import closing
from datetime import datetime

def is_good_response_json(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('json') > -1)

def simple_request(url):
    """
    Tries to use requests as an api call. Checks response to make sure it is good.

    Returns the response if good call, returns error if not.
    """

    try:
        with requests.get(url) as resp:
            if is_good_response_json(resp):
                return resp
            else:
                return None

    except RequestException as e:
        print('Error during requests to {0} : {1}'.format(url, str(e)))
        return None
    
server = 'localhost'
database = 'nathria_prog'
username = 'postgres'
password = 'postgres'

if 'conn' in locals():
    conn.close()
engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
conn = psycopg2.connect('host='+server+' dbname='+database+' user = '+username+' password='+password)
curs = conn.cursor()

curs.execute('select distinct guild_name from nathria_prog')
guilds = [item[0] for item in curs.fetchall()]

if 'coon' in locals():
    conn.close()
conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()

curs.execute("select * from nathria_prog where guild_name = '"+str(guilds[70])+"'")
guild_pulls = pd.DataFrame(curs.fetchall())
guild_pulls.columns = [desc[0] for desc in curs.description]

prog_hours = []
first_daily_pull = 0
pull_times = np.sort(guild_pulls['start_time'])
cur_day = datetime.fromtimestamp(pull_times[0]/1e3).day
for k, start_time in enumerate(pull_times):
    if datetime.fromtimestamp(start_time/1e3).day != cur_day:
        first_daily_pull_time = pull_times[first_daily_pull]
        last_daily_pull_time = pull_times[k-1]
        time_delta = datetime.fromtimestamp(last_daily_pull_time/1e3)-\
            datetime.fromtimestamp(first_daily_pull_time/1e3)



#%%