#%% First
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
from bs4 import BeautifulSoup

from dotenv import load_dotenv, dotenv_values
from requests_oauthlib import OAuth2, OAuth2Session

#%%
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

env_vars = dotenv_values('config.env')
client_id = env_vars['id']
client_secret = env_vars['secret']
code = env_vars['code']

callback_uri = "http://localhost:8080"
authorize_url = "https://www.warcraftlogs.com/oauth/authorize"
token_url = "https://www.warcraftlogs.com/oauth/token"

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

with open('..//get_guild_list/guild_list_hungering.json', encoding='utf-8') as f:
    guilds = json.load(f)

#%%
def get_guild_id(guild):
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
    start_time = fight['startTime']
    end_time = fight['endTime']
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
            stats = player['combatantInfo']['stats']
            primaries = ['Agility','Intellect','Strength']
            for primary in primaries:
                if primary in stats.keys():
                    break

            player_info = {}
            player_info= {'unique_id': unique_id,
                          'class': player['type'],
                          'spec': player['specs'][0],
                          'role': role,
                          'ilvl': player['minItemLevel'],
                          'primary': stats[primary]['min'],
                          'mastery': stats['Mastery']['min'],
                          'crit': stats['Crit']['min'],
                          'haste': stats['Haste']['min'],
                          'vers': stats['Versatility']['min'],
                          'stamina': stats['Stamina']['min']}
            player_list.append(player_info)
    return player_list



    comp_list = []
    for player in comp:
        comp_list.append((player['type'], player['specs']['spec'], player['specs']['role']))

    
    # fight_list = r.json()['data']['reportData']['report']['fights']


# %% Setup the SQL Stuff
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
    already_added_guilds = [item[0] for item in curs.fetchall()]
    already_added_length = len(already_added_guilds)
else:
    already_added_guilds = []
    already_added_length = 0

def check_in_sql(unique_id):
    curs.execute('select * from nathria_prog_v2 where unique_id == "%s"' % (unique_id))
    return True if curs.fetchone()[0] else False

def add_to_sql(curs, table, info):
    placeholders = ', '.join(['%s'] * len(info))
    columns = ', '.join(info.keys())
    sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % ('nathria_prog_v2', columns, placeholders)
    # valid in Python 3
    curs.execute(sql, list(info.values()))

# for guild in guilds[725]:
guild = guilds[725]
log_list = get_log_list(guild)
for log in log_list:
    fight_list = get_pulls(log, guild)
    for fight in fight_list:
        fight['unique_id'] = fight['log_code'] + '_' + str(fight['id'])
        if check_in_sql(fight['unique_id']):
            continue

        player_info = get_fight_info(fight, guild, fight['unique_id'])




        asdfasdfsaf

# for guild in guilds[725]:
#     log_list = get_log_list(guild)
#     for log in log_list:
#         fight_list = get_pulls(log, guild)
#         for fight in fight_list:
#             fight_info = get_fight_info(fight, guild)
#             asdfasdfsaf

#%%
# DC is guild 725
guild_num = 725
guild_info = {'guild_name': guilds[guild_num]['name'],
              'realm': guilds[guild_num]['realm'].replace(' ','-'),
              'region': guilds[guild_num]['region']}

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

 #%%
# %%
