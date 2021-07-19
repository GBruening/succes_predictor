#%% First
import numpy as np
import json
import os
import pandas as pd
import requests
from contextlib import closing
import time
from datetime import datetime
import seaborn as sns

bosslist = []
bosslist.append({'boss': 'shriek',
                 'id':   '2398'})
bosslist.append({'boss': 'hunt',
                 'id':   '2418'})
bosslist.append({'boss': 'sun_king',
                 'id':   '2402'})
bosslist.append({'boss': 'art',
                 'id':   '2405'})
bosslist.append({'boss': 'innvera',
                 'id':   '2406'})
bosslist.append({'boss': 'council',
                 'id':   '2412'})
bosslist.append({'boss': 'sludge',
                 'id':   '2399'})
bosslist.append({'boss': 'slg',
                 'id':   '2417'})
bosslist.append({'boss': 'sire',
                 'id':   '2407'})

with open('get_guild_list/guild_list_hungering.json', encoding='utf-8') as f:
    guilds = json.load(f)

# guild_info = {'guild_name': 'Dinosaur Cowboys',
#               'realm': 'Area-52',
#               'region': 'US'}

guild_info = {'guild_name': guilds[725]['name'],
              'realm': guilds[725]['realm'].replace(' ','-'),
              'region': guilds[725]['region']}

with open('..//Warcraftlogs//api_key.txt.') as f:
    api_key = f.readlines()[0]

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
fight_link = 'https://www.warcraftlogs.com:443/v1/report/fights/'

pull_df = []
sl_release_ms = datetime.fromisoformat('2020-11-20').timestamp()*1000
past_day = 0

fight_starts_ms = []
for k, single_log in enumerate(log_list):
    if single_log['start'] < sl_release_ms:
        break
    date = datetime.fromtimestamp(single_log['start']/1000)
    log_start_ms = single_log['start']
    fight_id = single_log['id']
    log = simple_request(fight_link + fight_id + '?api_key=' + api_key)
    time.sleep(1)

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
    print(k)

pull_df = pd.DataFrame(pull_df)

# plot_data = pull_df.query('name == "Sludgefist"')#.query('start_time < 1.614e12')
# plot_data.insert(loc=0, column='pull_num', value=np.arange(len(plot_data)))
# sns.scatterplot(data = plot_data, x = 'start_time', y = 'end_perc')

# %% Save the DC pulls as json so I don't have to pull every time
DC_json_pulls = pull_df.to_json()
with open('DC_pulls.json', 'w', encoding = 'utf-8') as f:
        json.dump(DC_json_pulls, f, ensure_ascii=False, indent = 4)

# %% Start making the plots

with open('DC_pulls.json', encoding = 'utf-8') as f:
    DC_pulls = json.load(f)
DC_pulls = pd.read_json(DC_pulls)

def get_prog_pulls(data_df, boss_name):
    kills_df = data_df.query('name == "'+boss_name+'"').query('zoneDifficulty == 5').query('kill == True')
    first_kill_time = min(kills_df['end_time'])
    return data_df.query('name == "'+boss_name+'"').query('zoneDifficulty == 5').query('start_time < '+str(first_kill_time))

def add_pull_num(data_df):
    data_df = data_df.sort_values(by = ['start_time'])
    data_df.insert(loc = 0, column = 'pull_num', value = np.arange(len(data_df))+1)
    return data_df

temp = add_pull_num(get_prog_pulls(pull_df,'Sludgefist'))
sns.scatterplot(data = temp, x = 'pull_num', y = 'end_perc')

# %%
