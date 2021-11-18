# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
#%%

import joblib
import regex as re
import pandas as pd

import numpy as np
import json
import os
import pandas as pd
import requests
from contextlib import closing
import time
from datetime import datetime
from requests.models import HTTPBasicAuth
import seaborn as sns
from matplotlib import pyplot as plt
from requests import get
from requests_futures.sessions import FuturesSession
from bs4 import BeautifulSoup

from dotenv import load_dotenv, dotenv_values
from requests_oauthlib import OAuth2, OAuth2Session

import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

#%% Create Data
from sqlalchemy import create_engine
import psycopg2
server = 'localhost'
database = 'nathria_prog'
username = 'postgres'
password = 'postgres'


pulls_all = pd.read_csv('nathria_prog_small.csv')
guilds = pulls_all['guild_name'].unique()

if 'conn' in locals():
    conn.close()
engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
curs1 = conn.cursor()
curs2 = conn.cursor()

curs1.execute("select * from nathria_prog_v2 where kill = 'True'")

pull_df = pd.DataFrame(curs1.fetchall())
pull_df.columns = [desc[0] for desc in curs1.description]
pull_df.unique_id = pull_df['log_code'].astype(str)+'_'+pull_df['pull_num'].astype(str)
pull_df['kill_time'] = pull_df['log_start']+pull_df['end_time']

only_first_kill = pull_df.groupby(['guild_name', 'name']).head(1)
only_first_kill = only_first_kill[only_first_kill.guild_name.isin(guilds)]

kill_guilds = only_first_kill['guild_name'].unique()
curs1.execute("select * from nathria_prog_v2 where kill = 'False'")
pull_df = pd.DataFrame(curs1.fetchall())
pull_df.columns = [desc[0] for desc in curs1.description]
pull_df.unique_id = pull_df['log_code'].astype(str)+'_'+pull_df['pull_num'].astype(str)
pull_df['kill_time'] = pull_df['log_start']+pull_df['end_time']

only_last_pull = pull_df.groupby(['guild_name', 'name']).tail(1)
only_last_pull = only_last_pull[~pull_df.guild_name.isin(kill_guilds)]
only_last_pull = only_last_pull[only_last_pull.guild_name.isin(guilds)]

output = pd.concat([only_first_kill, only_last_pull])
# output.to_sql('only_last_pull_small', engine)


#%%


env_vars = dotenv_values('config.env')
client_id = env_vars['id']
client_secret = env_vars['secret']
code = env_vars['code']

callback_uri = "http://localhost:8080"
authorize_url = "https://www.warcraftlogs.com/oauth/authorize"
token_url = "https://www.warcraftlogs.com/oauth/token"

if os.path.isfile('refresh_token.env'):
    env_vars = dotenv_values('refresh_token.env')
    refresh_token = env_vars['refresh_token']
    access_token = env_vars['access_token']
else:
    raise 'Get your fresh token dumby'

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
    # session = FuturesSession(max_workers = 2)
    # futures = [session.post(**get_fight_args(fight, graphql_endpoint, headers)) for fight in fights_list]

    # fights_tables = []
    # for k, item in enumerate(futures):
    #     if k % 100 == 0:
    #         print(k)
    #     result = item.result()
    #     if result.status_code!=200:
    #         print(result.status_code)
    #     # if is_good_response_json(item.result()):
    #     try:
    #         fights_tables.append(result.json()['data']['reportData']['report']['table']['data'])
    #     except:
    #         pass
    # return fights_tables

    session = FuturesSession(max_workers = 1)
    fights_tables = []
    for k, fight in enumerate(fights_list):
        item = session.post(**get_fight_args(fight, graphql_endpoint, headers))
        if k % 100 == 0:
            print(k)
        result = item.result()
        if int(result.headers['X-RateLimit-Remaining']) < 10:
            print('sleeping')
            time.sleep(60)
        if result.status_code!=200:
            print(result.status_code)
        # if is_good_response_json(item.result()):
        try:
            fights_tables.append(result.json()['data']['reportData']['report']['table']['data'])
        except:
            pass
    return fights_tables

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
                        'name': player['name'],
                        'guild_name': guild_name,
                        'server': player['server'],
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
                        'boss_name': boss_name}
            player_list.append(player_info)
    return player_list


fights_list = output.to_dict('records') 
asdfasdf
fights_tables = get_fight_table(fights_list, graphql_endpoint, headers)

playerdf = pd.DataFrame()
for q, table in enumerate(fights_tables):
    if q % 100 == 0:
        print(q)
    unique_id = fights_list[q]['unique_id']
    guild_name = fights_list[q]['guild_name']
    player_info = parse_fight_table(table, fights_list[q]['name'], unique_id, guild_name)
    playerdf = playerdf.append(pd.DataFrame(player_info))
            
playerdf.to_csv('only_first_kill_players.csv')

# for guild_name in logged_guilds:
#     curs.execute(f"select * from nathria_prog_v2 where guild_name = '{guild_name}'")
#     pulls = pd.DataFrame(curs.fetchall())
#     pulls.columns = [desc[0] for desc in curs.description]
#     fights_list = pulls.to_dict('records')

#     curs.execute(f"select distinct unique_id from nathria_prog_v2_players where guild_name = '{guild_name}'")
#     added_fights = [item[0] for item in curs.fetchall()]
#     fight_list = [fight for fight in fights_list if fight['unique_id'] not in added_fights]
    
#     if len(fight_list)>1:
#         fights_tables = get_fight_table(fights_list, graphql_endpoint, headers)

#         playerdf = pd.DataFrame()
#         for q, table in enumerate(fights_tables):
#             unique_id = fights_list[q]['unique_id']
#             guild_name = guild_name
#             player_info = parse_fight_table(table, fights_list[q]['name'], unique_id, guild_name)
#             for player in player_info:
#                 for player in player_info:
#                     playerdf = playerdf.append(pd.DataFrame(player, index=['i',]))
#         if len(playerdf)>1:
#             print(f'Adding to SQL guild player info {guild["name"]}')
#         playerdf.to_sql('nathria_prog_v2_players', engine, if_exists='append')















#%%
if 'conn' in locals():
    conn.close()
engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
curs1 = conn.cursor()
curs2 = conn.cursor()

# curs2.execute("select * from only_last_pull_small \
#     left join nathria_prog_v2_players \
#         on only_last_pull_small.unique_id = nathria_prog_v2_players.unique_id;")
# only_first_kill_players = pd.DataFrame(curs2.fetchall())
# only_first_kill_players.columns = [desc[0] for desc in curs2.description]
# only_first_kill_players

# only_first_kill_players.to_sql('only_first_kill_players', engine)
# only_first_kill_players.to_csv('only_first_kill_players.csv')

only_first_kill_players = pd.read_csv('only_first_kill_players.csv')
