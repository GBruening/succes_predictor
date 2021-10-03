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

print(refresh_token)
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

if r.status_code == 200:
    test = r.json()
    print(json.dumps(r.json(), indent=2))

print(refresh_token)

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

def get_fight_info(fight, guild):
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
            player_info= {'class': player['type'],
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



    comp_list = []
    for player in comp:
        comp_list.append((player['type'], player['specs']['spec'], player['specs']['role']))

    
    # fight_list = r.json()['data']['reportData']['report']['fights']

for guild in guilds:
    guild = guilds[725]
    query = ("{"
    f"reportData{{"
    f"    reports(guildID: {guild['id']}, zoneID: 26){{"
    f"    data{{"
    f"        fights(difficulty: 5){{"
    f"        name"
    f"        averageItemLevel"
    f"        id"
    f"        }}"
    f"    }}"
    f"    }}"
    f"}}"
    f"}}")
    r = requests.post(graphql_endpoint, json={"query": query}, headers=headers)    

    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2))

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
