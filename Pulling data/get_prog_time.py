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
    
    curs.execute("select * from nathria_prog where guild_name = '"+guild_name+"'")
    guild_pulls = pd.DataFrame(curs.fetchall())
    guild_pulls.columns = [desc[0] for desc in curs.description]

    daily_hours = []
    weekly_hours = []
    first_daily_pull = 0
    pull_times = np.sort(guild_pulls['start_time'])
    pull_end_times = np.sort(guild_pulls['end_time'])
    cur_day = datetime.fromtimestamp(pull_times[0]/1e3).day
    cur_week = datetime.fromtimestamp(pull_times[0]/1e3).isocalendar()[1]

    for k, row in guild_pulls.sort_values(by = 'start_time').iterrows():
        if datetime.fromtimestamp(row['start_time']/1e3).day != cur_day:
            first_daily_pull_time = pull_times[first_daily_pull]
            last_daily_pull_time = pull_end_times[k-1]
            time_delta = datetime.fromtimestamp(last_daily_pull_time/1e3)-\
                datetime.fromtimestamp(first_daily_pull_time/1e3)
            if time_delta.total_seconds()/3600 > 10:
                break
            daily_hours.append(time_delta.total_seconds()/3600)
            cur_day = datetime.fromtimestamp(row['start_time']/1e3).day
            first_daily_pull = k
        if datetime.fromtimestamp(row['start_time']/1e3).isocalendar()[1] != cur_week:
            first_daily_pull_time = pull_times[first_daily_pull]
            last_daily_pull_time = pull_end_times[k-1]
            time_delta = datetime.fromtimestamp(last_daily_pull_time/1e3)-\
                datetime.fromtimestamp(first_daily_pull_time/1e3)
            if time_delta.total_seconds()/3600 > 10:
                break
            weekly_hours.append(time_delta.total_seconds()/3600)
            cur_day = datetime.fromtimestamp(row['start_time']/1e3).day
            first_daily_pull = k
    
    guild_daily_hours = int(stats.mode(np.round(np.array(daily_hours)*2)/2)[0])
    guild_weekly_hours = int(stats.mode(np.round(np.array(weekly_hours)*2)/2)[0])
    guild_hours = pd.DataFrame({
        'guild_name': guild_name,
        'daily_hours': guild_daily_hours,
        'weekly_hours': guild_weekly_hours
    })
    guild_hours.to_sql('nathria_guild_raid_hours', engine, if_exists = 'append', index = False)


def get_boss_prog_time(guild_name):

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
        'name': guild_pulls.groupby(['boss_num','name'],as_index=False).mean()['name'][1],
        'prog_time': boss_prog_time
    })
    boss_prog_df.to_sql('nathria_guild_bossprog_hours', engine, if_exists = 'append', index = False)

guild_hours = int(stats.mode(np.round(np.array(prog_hours)*2)/2)[0])

#%%