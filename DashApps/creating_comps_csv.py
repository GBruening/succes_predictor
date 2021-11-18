# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
#%%

import joblib
import regex as re

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
