# %%

# LSTM and CNN for sequence classification in the IMDB dataset
import numpy as np
import pandas as pd
import csv

import os
from sqlalchemy import create_engine
import psycopg2

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

#%% Functions

def rm_repeat_boss(df):
    df = df.sort_values(by = ['fight_start_time'])
    temp_df = pd.DataFrame()
    temp_df = temp_df.append(df.iloc[0])

    last_start = df.iloc[0]['fight_start_time']
    last_perc = df.iloc[0]['boss_perc']
    for index, row in df[1:].iterrows():
        if abs(row['fight_start_time'] - last_start)/1000 > 30:
            if row['boss_perc'] > 0 and row['boss_perc'] != last_perc:
                temp_df = temp_df.append(row)
                last_start = row['fight_start_time']
                last_perc = row['boss_perc']
            elif row['boss_perc'] == 0:
                temp_df = temp_df.append(row)
                last_start = row['fight_start_time']
                last_perc = row['boss_perc']

    temp_df = temp_df.reset_index(drop = True)
    temp_df['pull_num'] = temp_df.index+1
    return temp_df

def listify(df):
    pull_list = []
    kill_list = []

    n_fights = 10
    boss_perc = list(df['boss_perc'])
    kill = list(df['kill'])

    pulls = [100]*n_fights
    for k in range(len(boss_perc)-1):
        if k == 0:
            pass
        else:
            pulls.pop(0)
            pulls.append(df['boss_perc'][k])
        pull_list.append(pulls.copy())
        kill_list.append(kill[k+1])
    return pull_list, kill_list

# %% Setup
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


# %% Get the data sets
boss_names = ['Shriekwing', \
            'Huntsman Altimor',
            'Hungering Destroyer', \
            "Sun King's Salvation",
            "Artificer Xy'mox", \
            'Lady Inerva Darkvein', \
            'The Council of Blood', \
            'Sludgefist', \
            'Stone Legion Generals', \
            'Sire Denathrius']


for boss in reversed(boss_names):
    specific_boss = boss.replace("'", "''")
    curs.execute(f"Select name, pull_num, kill, boss_perc, average_item_level, guild_name, guild_realm, guild_region,\
        log_start+start_time as fight_start_time\
        from nathria_prog_v2 where name = '{specific_boss}';")

    pull_df = pd.DataFrame(curs.fetchall())
    pull_df.columns = [desc[0] for desc in curs.description]

    guilds_df = pull_df[['guild_name','guild_realm']].drop_duplicates()

    pull_list = []
    kill_list = []
    counter = 0

    for index, row in guilds_df.iterrows():
        guild = row[0]
        realm = row[1]
        one_guild_df = pull_df.query(f'guild_name == "{guild}"').\
            query(f'guild_realm == "{realm}"').\
            sort_values(by = ['fight_start_time'])
        one_guild_df = rm_repeat_boss(one_guild_df.copy())
        temp_pull, temp_kill = listify(one_guild_df.copy(deep = True))
        pull_list.extend(temp_pull)
        kill_list.extend(temp_kill)
        counter += 1
        if counter % 100 == 0:
            print(f'Boss: {boss}, Added #{counter} of {len(guilds_df)}')

    merged_pull_kill = [(pull_list[i], kill_list[i]) for i in range(0, len(kill_list))]
    with open('pull_list_'+str(boss.replace(' ','_'))+'.csv', 'w') as f:
        csv_out=csv.writer(f, lineterminator = '\n')
        csv_out.writerow(['pulls','kills'])
        csv_out.writerows(merged_pull_kill)
        # for row in merged_pull_kill:
        #     csv_out.writerow(row)

    # f.write(str(pull_list) + '\n')
asfasfasf
#%% Test reader
temp = pd.read_csv('pull_list_lady.csv')

pull_list = list(temp['pulls'])
kill_list = list(temp['kills'])