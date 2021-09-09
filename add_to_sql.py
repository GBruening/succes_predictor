#%% First
import numpy as np
import json
import os
from numpy.lib.type_check import _asfarray_dispatcher
import pandas as pd
import requests
from contextlib import closing
import time
from datetime import datetime
import seaborn as sns
from matplotlib import pyplot as plt

# %% Define Functions

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

def get_all_logs(guild_info, api_key):
    
    link = "https://www.warcraftlogs.com:443/v1/reports/guild/" +  \
            guild_info['guild_name'] + "/" + guild_info['realm'] + "/" + \
            guild_info['region'] + "?api_key=" + api_key
    guild_logs = requests.get(link)
    # if guild_logs.status_code != 200:
    #     raise Exception('Invalid guild info. Name: '+guild_info['guild_name'] + \
    #                     ', Realm: '+guild_info['realm'] + \
    #                     ', Region: '+guild_info['region'])
    log_list = guild_logs.json()

    fight_link = 'https://www.warcraftlogs.com:443/v1/report/fights/'
    pull_df = []
    sl_release_ms = datetime.fromisoformat('2020-11-20').timestamp()*1000
    sanctum_release_ms = datetime.fromisoformat('2021-06-05').timestamp()*1000
    past_day = 0

    fight_starts_ms = []
    for k, single_log in enumerate(log_list):
        if single_log['start'] < sl_release_ms:
            break
        if single_log['start'] > sanctum_release_ms:
            continue
        date = datetime.fromtimestamp(single_log['start']/1000)
        log_start_ms = single_log['start']
        fight_id = single_log['id']
        log = simple_request(fight_link + fight_id + '?api_key=' + api_key)
        time.sleep(.5)

        if log:
            log = log.json()
            log_day = datetime.fromtimestamp(log['start']/1000).day
            if log_day != past_day:
                log_day = past_day
                # fight_starts_ms = []
            if 'fights' in log.keys():
                for fight in log['fights']:
                    if fight['boss'] == 0 or fight['difficulty'] != 5 or \
                        (len(fight_starts_ms)>0 and \
                        np.min(abs(np.array(fight_starts_ms) - (log_start_ms+fight['start_time'])))<(30*1000)):
                        continue
                    else:
                        fight_starts_ms.append(log_start_ms+fight['start_time'])

                        if fight['boss'] != 0:
                            pull_df.append({'name': fight['name'],
                                            'kill': fight['kill'],
                                            'end_perc': fight['bossPercentage']/100,
                                            'zoneDifficulty': fight['difficulty'],
                                            'start_time': log_start_ms+fight['start_time'],
                                            'end_time': log_start_ms+fight['end_time']})
        if k % 25 == 0:
            print(k)
    return pd.DataFrame(pull_df)

def dump_to_json(df, guild_info, prog):
    json_pulls = df.to_json()
    if prog == 1:
        print('Dumping Json to: '+guild_info['guild_name']+'_prog_pulls.json')
        with open(guild_info['guild_name']+'_prog_pulls.json', 'w', encoding = 'utf-8') as f:
                json.dump(json_pulls, f, ensure_ascii=False, indent = 4)
    else:
        print('Dumping Json to: '+guild_info['guild_name']+'_prog_pulls.json')
        with open(guild_info['guild_name']+'_pulls.json', 'w', encoding = 'utf-8') as f:
                json.dump(json_pulls, f, ensure_ascii=False, indent = 4)

def add_boss_nums(df):

    boss_nums = [5, 3, 2, 6, 1, 10, 8, 9, 4, 7]
    boss_names = [
        'Shriekwing', \
        'Huntsman Altimor',
        'Hungering Destroyer', \
        "Sun King's Salvation",
        "Artificer Xy'mox", \
        'Lady Inerva Darkvein', \
        'The Council of Blood', \
        'Sludgefist', \
        'Stone Legion Generals', \
        'Sire Denathrius']

    for k, item in enumerate(boss_names):
        df.loc[df.index[df['name'] == item],'boss_num'] = k
        
    return df

def get_prog_pulls(df, boss_name):
    # if type(df.iloc[0]['start_time']) != 'int':
    #     df['start_time'] = [time.mktime(x.to_pydatetime().timetuple()) for x in df['start_time']]
    #     df['end_time']   = [time.mktime(x.to_pydatetime().timetuple()) for x in df['end_time']]
    kills_df = df.query('name == "'+boss_name+'"').query('zoneDifficulty == 5').query('kill == True')
    if len(kills_df['kill'])>0:
        first_kill_time = min(kills_df['start_time'])
    else:
        first_kill_time = min(df.query('name == "'+boss_name+'"')['start_time'])
    return df.query('name == "'+boss_name+'"').query('zoneDifficulty == 5').query('start_time <= '+str(first_kill_time))

def add_pull_num(df):
    df = df.sort_values(by = ['start_time'])
    df.insert(loc = 0, column = 'pull_num', value = np.arange(len(df))+1)
    return df

def combine_boss_df(df):
    boss_names = [
        'Shriekwing', \
        'Huntsman Altimor',
        'Hungering Destroyer', \
        "Sun King's Salvation",
        "Artificer Xy'mox", \
        'Lady Inerva Darkvein', \
        'The Council of Blood', \
        'Sludgefist', \
        'Stone Legion Generals', \
        'Sire Denathrius']
    only_prog = pd.DataFrame()
    for k, boss_name in enumerate(np.unique(df['name'])):
        if boss_name in boss_names and boss_name in np.unique(df['name']):
            only_prog = only_prog.append(add_pull_num(get_prog_pulls(df.copy(deep = True), boss_name)))
    return only_prog

# Open guild list
with open('get_guild_list/guild_list_hungering.json', encoding='utf-8') as f:
    guilds = json.load(f)

# %% Setup the SQL Stuff
from sqlalchemy import create_engine
import psycopg2
server = 'localhost'
database = 'nathria_prog'
username = 'postgres'
password = 'postgres'

engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()
curs.execute('select * from "nathria_prog";')
temp_df = pd.DataFrame(curs.fetchall())
temp_df.columns = [desc[0] for desc in curs.description]
np.unique(temp_df['guild_name'])

curs.execute('select distinct guild_name from nathria_prog')
already_added_guilds = [item[0] for item in curs.fetchall()]
already_added_length = len(already_added_guilds)
# %% Get new data.
# DC is guild 725
# for guild_num in np.arange(len(guilds)):
# guild_num = 1075
for guild_num in np.arange(1075,len(guilds)):
    guild_info = {'guild_name': guilds[guild_num]['name'],
                'realm': guilds[guild_num]['realm'].replace(' ','-').replace("'",''),
                'region': guilds[guild_num]['region']}
    if not guild_info['guild_name'] in already_added_guilds:
        print('Pulling data from '+guild_info['guild_name']+'. Number '+str(guild_num)+'.')
        with open('..//Warcraftlogs//api_key.txt.') as f:
            api_key = f.readlines()[0]

        try:
            pulls = get_all_logs(guild_info = guild_info, api_key = api_key)
        except:
            continue

        if len(pulls) != 0:
            pulls['boss_num'] = np.zeros(len(pulls))

            pulls = add_boss_nums(pulls)

            prog_pulls = combine_boss_df(pulls.copy(deep = True))
            prog_pulls['guild_name'] = guild_info['guild_name']

            # if not guild_info['guild_name'] in np.unique(already_added_guilds):
            print('Adding guild '+guild_info['guild_name']+' to nathria_prog postgressql table.')
            prog_pulls.to_sql('nathria_prog', engine, if_exists='append')

            curs.execute('select distinct guild_name from nathria_prog')
            pull_length = len([item[0] for item in curs.fetchall()])
            # if already_added_length == pull_length:
            #     break
            # else:
            #     already_added_length = pull_length
        # except:
            # print("Couldn't pull Name: "+guild_i6+52
            # nfo['guild_name'] + \
            #             ', Realm: '+guild_info['realm'] + \
            #             ', Region: '+guild_info['region'])



#%% Filling in with 0's
fdsa
from sqlalchemy import create_engine
import psycopg2
server = 'localhost'
database = 'nathria_prog'
username = 'postgres'
password = 'postgres'

if 'conn' in locals():
    conn.close()
engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()

curs.execute('select * from "nathria_prog";')
padded_df = pd.DataFrame(curs.fetchall())
padded_df.columns = [desc[0] for desc in curs.description]

for boss_num in np.unique(df['boss_num']):
    boss_df = df.query('boss_num == '+str(boss_num))
    max_pulls = max(boss_df['pull_num'])
    for guild in np.unique(boss_df['guild_name']):
        print('Boss Number: '+str(boss_num)+' Guild: '+str(guild))
        guild_df = boss_df.query('guild_name == "'+str(guild)+'"')
        max_guild_pull = max(guild_df['pull_num'])
        df_add = guild_df.loc[np.repeat(guild_df.index.values[-1],max_pulls-max_guild_pull)]
        df_add['pull_num'] = [item+k+1 for k, item in enumerate(df_add['pull_num'])]
        guild_df.to_sql('nathria_prog_padded', engine, if_exists = 'append', index = False)
        df_add.to_sql('nathria_prog_padded', engine, if_exists = 'append', index = False)
        padded_df = padded_df.append(df_add, ignore_index = True)

#%% Avg/STD sql addition

if 'conn' in locals():
    conn.close()
engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()

curs.execute('select * from "nathria_prog_padded";')
df = pd.DataFrame(curs.fetchall())
df.columns = [desc[0] for desc in curs.description]

avg_df = df.groupby(['pull_num','boss_num'], as_index=False).mean()
sd_df = df.groupby(['pull_num','boss_num'], as_index=False).std()

avg_df.to_sql('nathria_prog_avg', engine, if_exists = 'replace', index = False)
sd_df.to_sql('nathria_prog_std', engine, if_exists = 'replace', index = False)