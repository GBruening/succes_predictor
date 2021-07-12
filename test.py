#%% First
import numpy as np
import json
import os
import pandas as pd
import requests

guild_info = {'guild_name': 'Dinosaur Cowboys',
              'realm': 'Area-52',
              'region': 'US'}

api_key = '3cd25babb96e24aefff5bc1e007f8359'

link = "https://www.warcraftlogs.com:443/v1/reports/guild/" +  \
        guild_info['guild_name'] + "/" + guild_info['realm'] + "/" + \
        guild_info['region'] + "?api_key="
guild_logs = requests.get(link + api_key)
log_list = guild_logs.json()

log_list[0]

#%%

fight_link = 'https://www.warcraftlogs.com:443/v1/report/fights/'
fight_id = log_list[1]['id']

log = requests.get(fight_link + fight_id + '?api_key=' + api_key)
# log.json()
log = log.json()
log.keys()

#%%

df_list = []
for fight in log['fights']:
    if fight['boss'] != 0:
        df_list.append({'name': fight['name'],
                        'kill': fight['kill']})


# %%
