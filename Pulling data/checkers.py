#%%

from os import stat_result
import numpy as np
import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import requests
from contextlib import closing
from datetime import datetime
from scipy import stats
from matplotlib import pyplot as plt


server = 'localhost'
database = 'nathria_prog'
username = 'postgres'
password = 'postgres'

if 'conn' in locals():
    conn.close()
engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
conn = psycopg2.connect('host='+server+' dbname='+database+' user = '+username+' password='+password)
curs = conn.cursor()

# %% CHeck start times for nathria prog and fix date string times

# curs.execute("select * from nathria_prog where guild_name = 'Dinosaur Cowboys'")
curs.execute("select * from nathria_prog where start_time < 1e10")
data = pd.DataFrame(curs.fetchall())
if len(data) > 0:
    data.columns = [desc[0] for desc in curs.description]

    for index, row in data.iterrows():
        print(str(row['name'] + ' ' + str(row['pull_num'])))
        curs.execute("update nathria_prog set start_time = %g, end_time = %g where "\
            "guild_name = '%s' and boss_num = %s and pull_num = %g" \
                % (row['start_time']*1e3, row['end_time']*1e3, row['guild_name'], row['boss_num'], row['pull_num']))



# %% Simple plot checks
curs.execute('select * from nathria_guild_raid_hours')
data = pd.DataFrame(curs.fetchall())
data.columns = [desc[0] for desc in curs.description]
plt.hist(data['weekly_hours'])

curs.execute('select * from nathria_guild_bossprog_hours')
data = pd.DataFrame(curs.fetchall())
data.columns = [desc[0] for desc in curs.description]
plt.hist(data['weekly_hours'])

#%%
