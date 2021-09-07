#%%
import numpy as np
import json
import os
import pandas as pd
import time
from datetime import datetime
import seaborn as sns
from matplotlib import pyplot as plt

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
temp_df = pd.DataFrame(curs.fetchall())
temp_df.columns = [desc[0] for desc in curs.description]

avg_df = temp_df.groupby(['pull_num','boss_num'], as_index=False).mean()
sd_df = temp_df.groupby(['pull_num','boss_num'], as_index=False).std()

g = sns.FacetGrid(avg_df, col = 'boss_num', col_wrap = 4, sharex=False, sharey=True)
g.map(sns.regplot, 'pull_num','end_perc', lowess = True, scatter = False,
    scatter_kws = {'color': 'black'},
    line_kws = {'color': 'red'})

# g = sns.FacetGrid(sd_df, col = 'boss_num', col_wrap = 4, sharex=False, sharey=True)
# g.map(sns.scatterplot, 'pull_num','end_perc')
# g.map(sns.regplot, 'pull_num','end_perc', lowess = True, scatter = False,
#     scatter_kws = {'color': 'black'},
#     line_kws = {'color': 'blue'})
# g.fig.suptitle(guild_info['guild_name']+' Castle Nathria Prog', size = 20)

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

for k, ax in enumerate(g.axes.flat):
    avg_mean = avg_df.query('boss_num == '+str(k))['end_perc']
    sd_end_perc = sd_df.query('boss_num == '+str(k))['end_perc']
    sd_pull = sd_df.query('boss_num == '+str(k))['pull_num']
    ax.fill_between(x = sd_pull, y1 = avg_mean-sd_end_perc, y2 = avg_mean + sd_end_perc)
    # ax.scatter(x = 'pull_num', y = 'end_perc', lowess = True)

axes = g.axes.flatten()
for k, ax in enumerate(axes):
    ax.set_ylabel("Wipe Percent")
    ax.set_xlabel("Pull Number")
    ax.set_title(boss_names[k])
plt.tight_layout()

#%%