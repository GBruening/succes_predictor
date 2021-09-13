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

if 'conn' in locals():
    conn.close()
conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()

def get_prog_hours(guild_name):
    
    sql_table_exist = curs.execute("select exists(select * from information_schema.tables where table_name=%s)",\
        ('nathria_guild_raid_hours',))
    if curs.fetchone()[0]:
        curs.execute("select * from nathria_guild_raid_hours where guild_name = '"+str(guild_name)+"'")
        guild_already_added = pd.DataFrame(curs.fetchall())
        guild_already_added.columns = [desc[0] for desc in curs.description]
    else:
        guild_already_added = []        

    if len(guild_already_added) == 1:
        print('Guild: '+str(guild_name)+' already in SQL table. Continuing...')
        return None

    curs.execute("select * from nathria_prog where guild_name = '"+guild_name+"'")
    guild_pulls = pd.DataFrame(curs.fetchall())
    guild_pulls.columns = [desc[0] for desc in curs.description]
    guild_pulls = guild_pulls.sort_values(by = ['boss_num','pull_num'])

    daily_hours = []
    weekly_hours = [0]
    first_daily_pull = 0
    pull_times = np.sort(guild_pulls['start_time'])
    pull_end_times = np.sort(guild_pulls['end_time'])
    cur_day = datetime.fromtimestamp(pull_times[0]).day
    cur_week = datetime.fromtimestamp(pull_times[0]).isocalendar()[1]

    days = [datetime.fromtimestamp(x).day for x in pull_times]
    weeks = [datetime.fromtimestamp(x).isocalendar()[1] for x in pull_times]

    cur_day = days[0]
    cur_week = weeks[0]
    for k, day in enumerate(days):
        if day != cur_day:
            time_delta = datetime.fromtimestamp(pull_end_times[k-1])-\
                datetime.fromtimestamp(pull_times[first_daily_pull])
            if time_delta.total_seconds()/3600 > 10:
                break
            daily_hours.append(time_delta.total_seconds()/3600)
            cur_day = day
            first_daily_pull = k

            if weeks[k] != cur_week:
                weekly_hours.append(0)
                cur_week = weeks[k]

            if len(weekly_hours)>0:
                weekly_hours[-1] += time_delta.total_seconds()/3600
            else:
                weekly_hours[0] += time_delta.total_seconds()/3600

    
    guild_daily_hours = int(stats.mode(np.round(np.array(daily_hours)*2)/2)[0])
    guild_weekly_hours = int(stats.mode(np.round(np.array(weekly_hours)*2)/2)[0])
    guild_hours = pd.DataFrame({
        'guild_name': [guild_name],
        'daily_hours': [guild_daily_hours],
        'weekly_hours': [guild_weekly_hours]
    })
    print('Adding guild '+str(guild_name)+' to nathria_guild_raid_hours.')
    guild_hours.to_sql('nathria_guild_raid_hours', engine, if_exists = 'append', index = False)

def get_boss_prog_time(guild_name):
    
    sql_table_exist = curs.execute("select exists(select * from information_schema.tables where table_name=%s)",\
        ('nathria_guild_bossprog_hours',))
    if curs.fetchone()[0]:
        curs.execute("select * from nathria_guild_bossprog_hours where guild_name = '"+str(guild_name)+"'")
        guild_already_added = pd.DataFrame(curs.fetchall())
        guild_already_added.columns = [desc[0] for desc in curs.description]
    else:
        guild_already_added = []        

    if len(guild_already_added) == 10:
        print('Guild: '+str(guild_name)+' already in SQL table. Continuing...')
        return None
    
    curs.execute("select * from nathria_prog where guild_name = '"+guild_name+"'")
    guild_pulls = pd.DataFrame(curs.fetchall())
    guild_pulls.columns = [desc[0] for desc in curs.description]

    daily_first_boss_pull = 0
    cur_boss_num = 0
    boss_prog_time = [0]*10

    for boss_num in range(0,10):
        boss_df = guild_pulls.query('boss_num == '+str(boss_num))
        starts = np.array(boss_df['start_time'])
        ends = np.array(boss_df['end_time'])
        if datetime.fromtimestamp(min(starts)/1e3).date() == datetime.fromtimestamp(max(ends)/1e3).date():
            time_delta = datetime.fromtimestamp(max(ends)/1e3)-\
                datetime.fromtimestamp(min(starts)/1e3)
            boss_prog_time[boss_num] += np.round(time_delta.total_seconds()/3600,5)
        
        first_start = 0
        cur_day = datetime.fromtimestamp(starts[0]/1e3).date()
        for k, start in enumerate(starts):
            if datetime.fromtimestamp(start/1e3).date() != cur_day:
                boss_prog_time[boss_num] += np.round((datetime.fromtimestamp(ends[k-1]/1e3)-\
                    datetime.fromtimestamp(starts[first_start]/1e3)).total_seconds()/3600,5)
                first_start = k
                cur_day = datetime.fromtimestamp(start/1e3).date()

        if k == len(starts):
            boss_prog_time[boss_num] += np.round((datetime.fromtimestamp(ends[k]/1e3)-\
                    datetime.fromtimestamp(starts[first_start]/1e3)).total_seconds()/3600,5)

    boss_prog_time = np.trunc(np.array(boss_prog_time)*1e5)/1e5
    boss_prog_df = pd.DataFrame({
        'name': guild_pulls.groupby(['boss_num','name'],as_index=False).mean()['name'],
        'prog_time': boss_prog_time, 
        'guild_name': guild_name
    })
    print('Adding guild '+str(guild_name)+' to nathria_guild_bossprog_hours.')
    boss_prog_df.to_sql('nathria_guild_bossprog_hours', engine, if_exists = 'append', index = False)




#%%