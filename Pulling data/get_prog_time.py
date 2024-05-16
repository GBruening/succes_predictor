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

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
try:
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
except:
    data = pd.read_csv(dname+'/nathria_prog_allpulls_small.csv')
    guilds = data['guild_name'].unique()
    
    pass

def get_prog_hours(guild_name, sql = True, guild_pulls = None):
    if sql:
        curs.execute("select exists(select * from information_schema.tables where table_name=%s)",\
            ('nathria_guild_raid_hours',))
        if curs.fetchone()[0]:
            curs.execute("select * from nathria_guild_raid_hours where guild_name = '"+str(guild_name)+"'")
            guild_already_added = pd.DataFrame(curs.fetchall())
            if len(guild_already_added) == 1:
                print('Guild: '+str(guild_name)+' already in SQL table. Continuing...')
                return None     

        curs.execute("select * from nathria_prog where guild_name = '"+guild_name+"'")
        guild_pulls = pd.DataFrame(curs.fetchall())
        guild_pulls.columns = [desc[0] for desc in curs.description]
    elif guild_pulls is None:
        raise(f'Not sql and guild pulls is non in get prog hours.')

    guild_pulls = guild_pulls.sort_values(by = ['boss_num','pull_num'])

    if len(guild_pulls)< 50:
        return None

    daily_hours = []
    weekly_hours = [0]
    first_daily_pull = 0
    pull_times = np.sort(guild_pulls['start_time'])
    pull_end_times = np.sort(guild_pulls['end_time'])
    if pull_times[0]< 1e10:
        pull_times = pull_times * 1e3
        pull_end_times = pull_end_times * 1e3
    cur_day = datetime.fromtimestamp(pull_times[0]/1e3).day
    cur_week = datetime.fromtimestamp(pull_times[0]/1e3).isocalendar()[1]


    days = [datetime.fromtimestamp(x/1e3).timetuple().tm_yday for x in pull_times]
    weeks = [datetime.fromtimestamp(x/1e3).isocalendar()[1] for x in pull_times]

    prev_pull = pull_times[0]
    for k, pull_start in enumerate(pull_times):        
        time_delta = datetime.fromtimestamp(pull_start/1e3)-\
            datetime.fromtimestamp(prev_pull/1e3)
        if time_delta.total_seconds()/3600 > 3:
            time_delta = datetime.fromtimestamp(pull_end_times[k-1]/1e3)-\
                datetime.fromtimestamp(pull_times[first_daily_pull]/1e3)
            # if time_delta.total_seconds()/3600 > 14:
            #     daily_hours.append(time_delta.total_seconds()/3600)
            daily_hours.append(time_delta.total_seconds()/3600)
            # cur_day = day
            first_daily_pull = k

            if weeks[k] != cur_week:
                weekly_hours.append(0)
                cur_week = weeks[k]

            if len(weekly_hours)>0:
                weekly_hours[-1] += time_delta.total_seconds()/3600
            else:
                weekly_hours[0] += time_delta.total_seconds()/3600
        prev_pull = pull_start


    # cur_day = days[0]
    # cur_week = weeks[0]
    # for k, day in enumerate(days):
    #     if day != cur_day:
    #         time_delta = datetime.fromtimestamp(pull_end_times[k-1]/1e3)-\
    #             datetime.fromtimestamp(pull_times[first_daily_pull]/1e3)
    #         # if time_delta.total_seconds()/3600 > 14:
    #         #     daily_hours.append(time_delta.total_seconds()/3600)
    #         daily_hours.append(time_delta.total_seconds()/3600)
    #         cur_day = day
    #         first_daily_pull = k

    #         if weeks[k] != cur_week:
    #             weekly_hours.append(0)
    #             cur_week = weeks[k]

    #         if len(weekly_hours)>0:
    #             weekly_hours[-1] += time_delta.total_seconds()/3600
    #         else:
    #             weekly_hours[0] += time_delta.total_seconds()/3600

    
    guild_daily_hours = int(stats.mode(np.round(np.array(daily_hours)*2)/2)[0])
    guild_weekly_hours = int(stats.mode(np.round(np.array(weekly_hours)*2)/2)[0])
    guild_hours = pd.DataFrame({
        'guild_name': [guild_name],
        'daily_hours': [guild_daily_hours],
        'weekly_hours': [guild_weekly_hours]
    })
    try:
        guild_hours.to_sql('nathria_guild_raid_hours', engine, if_exists = 'append', index = False)
        print('Adding guild '+str(guild_name)+' to nathria_guild_raid_hours.')
    except:
        print(f'Didnt add to sql.')
        return(guild_hours)

def get_boss_prog_time(guild_name, sql = True, guild_pulls = None):
    
    if sql:
        sql_table_exist = curs.execute("select exists(select * from information_schema.tables where table_name=%s)",\
            ('nathria_guild_bossprog_hours',))
        if curs.fetchone()[0]:
            curs.execute("select * from nathria_guild_bossprog_hours where guild_name = '"+str(guild_name)+"'")
            guild_already_added = pd.DataFrame(curs.fetchall())
            if len(guild_already_added) == 1:
                print('Guild: '+str(guild_name)+' already in SQL table. Continuing...')
                return None    

        
        curs.execute("select * from nathria_prog where guild_name = '"+guild_name+"'")
        guild_pulls = pd.DataFrame(curs.fetchall())
        guild_pulls.columns = [desc[0] for desc in curs.description]

    if len(guild_pulls)< 50:
        return None
        
    daily_first_boss_pull = 0
    cur_boss_num = 0
    boss_prog_time = [0]*10
    bosses_seen = np.sort(np.unique(guild_pulls['boss_num'])).astype(int)
    for boss_num in bosses_seen:
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
        'boss_num': bosses_seen,
        'prog_time': boss_prog_time[bosses_seen], 
        'guild_name': guild_name
    })
    try:
        boss_prog_df.to_sql('nathria_guild_bossprog_hours', engine, if_exists = 'append', index = False)
        print('Adding guild '+str(guild_name)+' to nathria_guild_bossprog_hours.')
    except:
        print(f'Didnt add to sql.')
        return(boss_prog_df)   

#%%
for k, guild_name in enumerate(guilds):
    print('Pulling guild '+str(guild_name)+' Number '+str(k))
    get_prog_hours(guild_name)
    get_boss_prog_time(guild_name)

prog_hours = pd.DataFrame()
prog_boss_hours = pd.DataFrame()

for k, guild_name in enumerate(guilds):
    print('Pulling guild '+str(guild_name)+' Number '+str(k))
    try:
        prog_hours = pd.concat([prog_hours,get_prog_hours(guild_name, sql = False, guild_pulls=data.query("guild_name == @guild_name"))])    
        write_csv(prog_hours, 'prog_hours.csv')
    except:
        pass
    try:
        prog_boss_hours = pd.concat([prog_boss_hours,get_boss_prog_time(guild_name, sql = False, guild_pulls=data.query("guild_name == @guild_name"))])
        write_csv(prog_boss_hours, 'prog_boss_hours.csv')
    except:
        pass

# for guild in guilds:
#     try:
#         get_prog_hours(guild)
#     except:
#         pass
#     try:
#         get_boss_prog_time(guild)
#     except:
#         pass


#%%