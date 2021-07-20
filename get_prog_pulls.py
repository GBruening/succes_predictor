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
from matplotlib import pyplot as plt

with open('get_guild_list/guild_list_hungering.json', encoding='utf-8') as f:
    guilds = json.load(f)

# DC is guild 725
guild_num = 511
guild_info = {'guild_name': guilds[guild_num]['name'],
              'realm': guilds[guild_num]['realm'].replace(' ','-'),
              'region': guilds[guild_num]['region']}

with open('..//Warcraftlogs//api_key.txt.') as f:
    api_key = f.readlines()[0]

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
    if guild_logs.status_code != 200:
        raise Exception('Invalid guild info. Name: '+guild_info['guild_name'] + \
                        ', Realm: '+guild_info['realm'] + \
                        ', Region: '+guild_info['region'])
    log_list = guild_logs.json()

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
        print(k)
    return pd.DataFrame(pull_df)

pull_df = get_all_logs(guild_info = guild_info, api_key = api_key)

# %% Save the DC pulls as json so I don't have to pull every time
def dump_to_json(df, guild_info):
    json_pulls = df.to_json()
    print('Dumping Json to: '+guild_info['guild_name']+'_pulls.json')
    with open(guild_info['guild_name']+'_pulls.json', 'w', encoding = 'utf-8') as f:
            json.dump(json_pulls, f, ensure_ascii=False, indent = 4)

dump_to_json(pull_df, guild_info)

with open(guild_info['guild_name']+'_pulls.json', encoding = 'utf-8') as f:
    DC_pulls = json.load(f)
DC_pulls = pd.read_json(DC_pulls)
DC_pulls['boss_num'] = np.zeros(len(DC_pulls))

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

DC_pulls = add_boss_nums(DC_pulls)

def get_prog_pulls(df, boss_name):
    if type(df.iloc[0]['start_time']) != 'int':
        df['start_time'] = [time.mktime(x.to_pydatetime().timetuple()) for x in df['start_time']]
        df['end_time']   = [time.mktime(x.to_pydatetime().timetuple()) for x in df['end_time']]
    kills_df = df.query('name == "'+boss_name+'"').query('zoneDifficulty == 5').query('kill == True')
    first_kill_time = min(kills_df['start_time'])
    return df.query('name == "'+boss_name+'"').query('zoneDifficulty == 5').query('start_time <= '+str(first_kill_time))

def add_pull_num(df):
    df = df.sort_values(by = ['start_time'])
    df.insert(loc = 0, column = 'pull_num', value = np.arange(len(df))+1)
    return df

def combine_boss_df(df):
    only_prog = pd.DataFrame()
    for k, item in enumerate(np.unique(DC_pulls['name'])):
        only_prog = only_prog.append(add_pull_num(get_prog_pulls(df.copy(deep = True), item)))
    return only_prog

test1 = combine_boss_df(DC_pulls.copy(deep = True))

# %%
g = sns.FacetGrid(test1, col = 'boss_num', col_wrap = 4, sharex=False, sharey=True)
# g.map(sns.scatterplot, 'pull_num','end_perc', color = 'blue')
g.map(sns.regplot, 'pull_num','end_perc', lowess = True, 
    scatter_kws = {'color': 'black'},
    line_kws = {'color': 'blue'})
g.fig.suptitle(guild_info['guild_name']+' Castle Nathria Prog', size = 20)

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

# for ax in g.axes.flat:
#     ax.scatter(x = 'pull_num', y = 'end_perc', lowess = True)

axes = g.axes.flatten()
for k, ax in enumerate(axes):
    ax.set_ylabel("Wipe Percent")
    ax.set_xlabel("Pull Number")
    ax.set_title(boss_names[k])
plt.tight_layout()

# %%
