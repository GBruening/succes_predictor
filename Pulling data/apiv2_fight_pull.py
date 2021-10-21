#%% First
import numpy as np
import json
import os
import pandas as pd
import requests
from contextlib import closing
import time
import datetime
from requests.models import HTTPBasicAuth
import seaborn as sns
from matplotlib import pyplot as plt
from requests import get
from requests_futures.sessions import FuturesSession
from bs4 import BeautifulSoup
from concurrent.futures import as_completed
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from dotenv import load_dotenv, dotenv_values
from requests_oauthlib import OAuth2, OAuth2Session

#%%
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# warcraftlogs = OAuth2Session(client_id, redirect_uri=callback_uri)
# authorization_url, state = warcraftlogs.authorization_url(authorize_url,
#         access_type="offline")

# token = warcraftlogs.fetch_token(token_url = token_url,
#                                  auth = HTTPBasicAuth(client_id, client_secret),
#                                  code = code)
# access_token = token['access_token']
# refresh_token = token['refresh_token']
# with open('refresh_token.env', 'w') as f:
#     f.write('refresh_token = '+str(refresh_token)+'\nacces_token = '+str(access_token))

if os.path.isfile('refresh_token.env'):
    env_vars = dotenv_values('refresh_token.env')
    refresh_token = env_vars['refresh_token']
    access_token = env_vars['access_token']
else:
    raise 'Get your fresh token dumby'

env_vars = dotenv_values('config.env')
client_id = env_vars['id']
client_secret = env_vars['secret']
code = env_vars['code']

callback_uri = "http://localhost:8080"
authorize_url = "https://www.warcraftlogs.com/oauth/authorize"
token_url = "https://www.warcraftlogs.com/oauth/token"

# print(refresh_token)
try:
    warcraftlogs = OAuth2Session(client_id = client_id)
    graphql_endpoint = "https://www.warcraftlogs.com/api/v2/client"
    headers = {"Authorization": f"Bearer {access_token}"}

    query = """{
    reportData{
        reports(guildID: 95321, endTime: 1622872800000.0, startTime: 1605855600000.0){
        data{
            fights(difficulty: 5){
            name          
            averageItemLevel
            #   friendlyPlayers
            id
            }
        }
        }
    }
    }"""

    r = requests.post(graphql_endpoint, json={"query": query}, headers=headers)    
    if r.status_code == 401:
        raise 'Got 401 error'
except:
    token = warcraftlogs.refresh_token(token_url = token_url,
                                    auth = HTTPBasicAuth(client_id, client_secret),
                                    refresh_token = refresh_token)
    access_token = token['access_token']
    refresh_token = token['refresh_token']
    with open('refresh_token.env', 'w') as f:
        f.write('refresh_token = '+str(refresh_token)+'\naccess_token = '+str(access_token))
        
    warcraftlogs = OAuth2Session(client_id = client_id)
    graphql_endpoint = "https://www.warcraftlogs.com/api/v2/client"
    headers = {"Authorization": f"Bearer {access_token}"}

    query = """{
    reportData{
        reports(guildID: 95321, endTime: 1622872800000.0, startTime: 1605855600000.0){
        data{
            fights(difficulty: 5){
            name          
            averageItemLevel
            #   friendlyPlayers
            id
            }
        }
        }
    }
    }"""

    r = requests.post(graphql_endpoint, json={"query": query}, headers=headers)    
    if r.status_code == 401:
        raise 'Got 401 error'

with open('..//get_guild_list/guild_list_hungering.json', encoding='utf-8') as f:
    guilds = json.load(f)

#%%

def is_good_response_json(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('json') > -1)

def get_guild_id(guild):
    try:
        guild_id = int(guild['id'])
    except:
        query = """    
            {
            guildData{
                guild(name: "%s", serverSlug: "%s", serverRegion: "%s"){
                id
                }
            }
            }
        """ % (guild['name'], guild['realm'].replace(' ', '-'), guild['region'])
        r = requests.post(graphql_endpoint, json={"query": query}, headers=headers)
        guild_id = r.json()['data']['guildData']['guild']['id']
    return guild_id

def get_log_list(guild):
    guild['id'] = get_guild_id(guild)
    query = ("{"
    f"reportData{{"
    f"    reports(guildID: {guild['id']}, zoneID: 26){{"
    f"    data{{"
    f"        code"
    f"        startTime"
    f"        endTime"
    f"    }}"
    f"    }}"
    f"}}"
    f"}}")
    r = requests.post(graphql_endpoint, json={"query": query}, headers=headers)
    log_list = r.json()['data']['reportData']['reports']['data']

    return log_list

def get_log_list_apiv1(guild):
    with open('..//..//Warcraftlogs//api_key.txt.') as f:
            api_key = f.readlines()[0]
    
    link = "https://www.warcraftlogs.com:443/v1/reports/guild/" +  \
            guild['name'] + "/" + guild['realm'].replace(' ', '-').replace("'","")+ "/" + \
            guild['region'] + "?api_key=" + api_key

    guild_logs = requests.get(link)
    log_list = guild_logs.json()

    log_list_new = []
    for item in log_list:
        if item['zone'] == 26:
            log_list_new.append({'code': item['id'],
                                'startTime': item['start'],
                                'endTime': item['end']})
                
    return log_list_new

def get_pulls(log, guild):
    log_id = log['code']
    query = """
    {
    reportData{
        report(code: "%s"){
        fights(difficulty: 5){
            name
            id
            averageItemLevel
            bossPercentage
            kill
            startTime
            endTime
        }
        }
    }
    }
    """ % (log_id)

    r = requests.post(graphql_endpoint, json={"query": query}, headers=headers)
    fight_list = r.json()['data']['reportData']['report']['fights']
    for k in range(len(fight_list)):
        fight_list[k].update({'log_code': log_id})    
    return fight_list

def get_fight_info(fight, guild, unique_id):
    code = fight['log_code']
    fight_ID = fight['id']
    start_time = fight['start_time']
    end_time = fight['end_time']
    query = """
    {
    reportData{
        report(code: "%s"){
        table(fightIDs: %s, startTime: %s, endTime: %s)
        }
    }
    }
    """ % (code, fight_ID, str(start_time), str(end_time))
    r = requests.post(graphql_endpoint, json={"query": query}, headers=headers)
    table = r.json()['data']['reportData']['report']['table']['data']
    comp = table['composition']
    roles = table['playerDetails']
    player_list = []
    for role in roles:
        players = roles[role]
        for player in players:
            try:
                gear_ilvl = [piece['itemLevel'] for piece in player['combatantInfo']['gear']]
                ilvl = np.mean(gear_ilvl)
            except:
                try:
                    ilvl = player['minItemLevel']
                except:
                    ilvl = np.NaN

            try:
                covenant = player['combatantInfo']['covenantID']
            except:
                covenant = np.NaN

            try:
                spec = player['specs'][0]
            except:
                spec = np.NaN

            try:
                stats = player['combatantInfo']['stats']
                primaries = ['Agility','Intellect','Strength']
                for primary in primaries:
                    if primary in stats.keys():
                        break
                primary= stats[primary]['min']
                mastery= stats['Mastery']['min']
                crit= stats['Crit']['min']
                haste= stats['Haste']['min']
                vers= stats['Versatility']['min']
                stamina= stats['Stamina']['min']
            except:
                primary = np.NaN
                mastery = np.NaN
                crit = np.NaN
                haste = np.NaN
                vers = np.NaN
                stamina = np.NaN
        
            player_info= {'unique_id': unique_id,
                        'class': player['type'],
                        'spec': spec,
                        'role': role,
                        'ilvl': ilvl,
                        'covenant': covenant,
                        'primary': primary,
                        'mastery': mastery,
                        'crit': crit,
                        'haste': haste,
                        'vers': vers,
                        'stamina': stamina,
                        'boss_name': fight['name']}
            player_list.append(player_info)
    return player_list


# %% Setup the SQL Stuff
from sqlalchemy import create_engine
import psycopg2
server = 'localhost'
database = 'nathria_prog'
username = 'postgres'
password = 'postgres'

if 'conn' in locals():
    conn.close()
try:
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
    conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
except:
    engine = create_engine('postgresql://postgres:postgres@192.168.0.6:5432/nathria_prog')
    conn = psycopg2.connect('host=192.168.0.6 dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()

curs.execute("select exists(select * from information_schema.tables where table_name=%s)",\
    ('nathria_prog_v2',))
if curs.fetchone()[0]:
    curs.execute('select distinct guild_name from nathria_prog_v2')
    already_added_guilds = [item[0] for item in curs.fetchall()]
    already_added_length = len(already_added_guilds)
else:
    already_added_guilds = []
    already_added_length = 0

def check_in_sql(fight):
    unique_id = fight['unique_id']
    curs.execute("select * from nathria_prog_v2 where unique_id = '%s'" % (unique_id))
    if curs.fetchone() is None:
        check_one = False
    else:
        check_one = True

    curs.execute("select * from nathria_prog_v2 where start_time > %s and end_time < %s and guild_name = '%s';" \
        % (fight['start_time']-60, fight['end_time']+60, fight['guild_name']))
    if curs.fetchone() is None:
        check_two = False
    else:
        check_two = True
    check = check_one or check_two
    return check

def add_to_sql(curs, table, info):
    placeholders = ', '.join(['%s'] * len(info))
    columns = ', '.join(info.keys())
    sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % (str(table), columns, placeholders)
    curs.execute(sql, list(info.values()))

#%%

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

curs.execute("select exists(select * from information_schema.tables where table_name=%s)",\
    ('nathria_prog_v2',))
if curs.fetchone()[0]:
    curs.execute('select distinct guild_name from nathria_prog_v2')
    logged_guilds = [item[0] for item in curs.fetchall()]
else:
    logged_guilds = []
    
def make_fights_query(fight):
    code = fight['log_code']
    fight_ID = fight['id']
    start_time = fight['start_time']
    end_time = fight['end_time']
    query = """
    {
    reportData{
        report(code: "%s"){
        table(fightIDs: %s, startTime: %s, endTime: %s)
        }
    }
    }
    """ % (code, fight_ID, str(start_time), str(end_time))

    return query

def get_fight_args(log, graphql_endpoint, headers):
    args = {'url': graphql_endpoint,
            'json': {'query': make_fights_query(log)},
            'headers': headers}
    return args

def get_fight_table(fights_list, graphql_endpoint, headers):
    session = FuturesSession(max_workers = 1)
    futures = [session.post(**get_fight_args(fight, graphql_endpoint, headers)) for fight in fights_list]

    fights_tables = []
    for k, item in enumerate(futures):
        result = item.result()
        if result.status_code!=200:
            print(result.status_code)
        if result.status_code!=429:
            raise 'To fast go fix it'
        # if is_good_response_json(item.result()):
        try:
            fights_tables.append(result.json()['data']['reportData']['report']['table']['data'])
        except:
            pass
    return fights_tables

def get_fight_table_and_parse(fights_list, graphql_endpoint, headers):
    # session = FuturesSession(max_workers = 1)

    # retries = 5
    # status_forcelist = [429, 502]    
    # retry = Retry(
    #     total=retries,
    #     read=retries,
    #     connect=retries,
    #     respect_retry_after_header=True,
    #     status_forcelist=status_forcelist,
    # )
    # adapter = HTTPAdapter(max_retries=retry)
    # session.mount('http://', adapter)
    # session.mount('https://', adapter)

    # futures = [session.post(**get_fight_args(fight, graphql_endpoint, headers)) for fight in fights_list]
    
    player_list = []
    q = 0
    # for future in as_completed(futures):
    req_num = 0
    last_time = datetime.datetime.now()
    for fight in fights_list:
        # print(q)
        # if time_diff < 50000:
        #     # print(time_diff)
        #     time.sleep(0.05 - (time_diff/1e6))
        result = requests.post(**get_fight_args(fight, graphql_endpoint, headers))
        if 'X-RateLimit-Remaining' in result.headers.keys() and int(result.headers['X-RateLimit-Remaining'])<50:
            cur_time = datetime.datetime.now()
            time_diff = (cur_time - last_time).microseconds
            print('Hit rate limit, sleeping for a sec.')
            # time.sleep(60-(time_diff/1e6)+10)
            time.sleep(60)
            last_time = datetime.datetime.now()
        # last_time = datetime.datetime.now()
        if result.status_code!=200:
            time.sleep(5)
            print(result.status_code)
        else:
            cur_time = datetime.datetime.now()
        if result.status_code==429:
            print(result.status_code)
            time.sleep(10)
            result = requests.post(**get_fight_args(fight, graphql_endpoint, headers))
        try:
            table = result.json()['data']['reportData']['report']['table']['data']

            if q % 50 == 0:
                print(f'Parsing {guild_name}, fight # {q+1} of {len(fights_list)}')

            player_info = parse_fight_table(table, fights_list[q]['name'], fights_list[q]['unique_id'], guild_name)
            if len(player_list) == 0:
                player_list = player_info
            else:
                player_list.extend(player_info)
            q+=1
        except:
            pass

    return pd.DataFrame.from_dict(player_list)

def parse_fight_table(table, boss_name, unique_id, guild_name):

    comp = table['composition']
    roles = table['playerDetails']
    player_list = []
    for role in roles:
        players = roles[role]
        for player in players:
            try:
                gear_ilvl = [piece['itemLevel'] for piece in player['combatantInfo']['gear']]
                ilvl = np.mean(gear_ilvl)
            except:
                try:
                    ilvl = player['minItemLevel']
                except:
                    ilvl = np.NaN
            
            try:
                server = player['server']
                class_ = player['type']
            except:
                server = np.NaN
                class_ = np.NaN
            try:
                covenant = player['combatantInfo']['covenantID']
            except:
                covenant = np.NaN

            try:
                spec = player['specs'][0]
            except:
                spec = np.NaN

            try:
                stats = player['combatantInfo']['stats']
                primaries = ['Agility','Intellect','Strength']
                for primary in primaries:
                    if primary in stats.keys():
                        break
                primary= stats[primary]['min']
                mastery= stats['Mastery']['min']
                crit= stats['Crit']['min']
                haste= stats['Haste']['min']
                vers= stats['Versatility']['min']
                stamina= stats['Stamina']['min']
            except:
                primary = np.NaN
                mastery = np.NaN
                crit = np.NaN
                haste = np.NaN
                vers = np.NaN
                stamina = np.NaN
        
            player_info= {'unique_id': unique_id,
                        'player_name': player['name'],
                        'guild_name': guild_name,
                        'server': server,
                        'class': class_,
                        'spec': spec,
                        'role': role,
                        'ilvl': ilvl,
                        'covenant': covenant,
                        'primary': primary,
                        'mastery': mastery,
                        'crit': crit,
                        'haste': haste,
                        'vers': vers,
                        'stamina': stamina,
                        'boss_name': boss_name}
            player_list.append(player_info)
    return player_list


def futures_process_fight_table(fights_list, parsed_num, tot_len, graphql_endpoint, headers):
    session = FuturesSession(max_workers = 1)

    retries = 5
    status_forcelist = [429, 502]    
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        respect_retry_after_header=True,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    futures = [session.post(**get_fight_args(fight, graphql_endpoint, headers)) for fight in fights_list]

    player_list = []
    for q, future in enumerate(as_completed(futures)):
        parsed_num += 1
        if parsed_num % 100 == 0:
            print(f'Parsing {guild_name}, fight # {parsed_num+1} of {tot_len}')
        result = future.result()
        if result.status_code != 200:
            print(result.status_code)
        if result.status_code == 502:
            continue
        table = result.json()['data']['reportData']['report']['table']['data']
        player_info = parse_fight_table(table, fights_list[q]['name'], fights_list[q]['unique_id'], guild_name)
        if len(player_list) == 0:
            player_list = player_info
        else:
            player_list.extend(player_info)
    return player_list, result, parsed_num

def make_batches(list_, n):
    new_list = []
    for k in range(0, len(list_), n):
        new_list.append(list_[k:k+n])
    return new_list

def batch_process_fight_table(fights_list, graphql_endpoint, headers):
    fight = fights_list[0]
    batches = make_batches(fights_list, 550)
    player_list = []
    last_time = datetime.datetime.now()
    tot_len = len(fights_list)
    parsed_num = 0
    for batch_num, batch_fight in enumerate(batches):

        result = requests.post(**get_fight_args(fight, graphql_endpoint, headers))
        if 'X-RateLimit-Remaining' in result.headers.keys() and int(result.headers['X-RateLimit-Remaining'])<550:
            print('At rate limit, wait longer.')
            time.sleep(60)

        print(f'Parsing batch # {batch_num} of {len(batches)}')
        plist, fut, parsed_num = futures_process_fight_table(batch_fight, parsed_num, tot_len, graphql_endpoint, headers)
        cur_time = datetime.datetime.now()
        time_diff = (cur_time - last_time).seconds
        if time_diff < 60:
            print(f'Sleeping for {60-time_diff+3}.')
            for sleepy_time in range(60-time_diff+3):
                if sleepy_time % 10 == 0:
                    print('\r', f'Slept for {sleepy_time}')
                time.sleep(1)
        last_time = datetime.datetime.now()
        player_list.extend(plist)
    return pd.DataFrame.from_dict(player_list)

gnum = 0
guild_name = logged_guilds[gnum]
start_num = 1800
for gnum, guild_name in enumerate(logged_guilds[start_num:]):
    curs.execute(f"select * from nathria_prog_v2 where guild_name = '{guild_name}'")
    pulls = pd.DataFrame(curs.fetchall())
    pulls.columns = [desc[0] for desc in curs.description]
    fights_list = pulls.to_dict('records')

    curs.execute("select exists(select * from information_schema.tables where table_name=%s)",\
        ('nathria_prog_v2_players',))
    if curs.fetchone()[0]:
        curs.execute(f"select distinct unique_id from nathria_prog_v2_players where guild_name = '{guild_name}'")
        added_fights = [item[0] for item in curs.fetchall()]
    else:
        added_fights = []

    fights_list = [fight for fight in fights_list if fight['unique_id'] not in added_fights]
    
    if len(fights_list)>1:
        print(f'Pulling fight logs {guild_name}, #{gnum+1+start_num} of {len(logged_guilds)}.')

        playerdf = get_fight_table_and_parse(fights_list, graphql_endpoint, headers)
        # playerdf = batch_process_fight_table(fights_list, graphql_endpoint, headers)

        playerdf.to_sql('nathria_prog_v2_players', engine, if_exists='append')
        time.sleep(180)

#%%