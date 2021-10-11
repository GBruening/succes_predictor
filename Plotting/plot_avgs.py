#%%
import numpy as np
import json
import os
import pandas as pd
import time
from datetime import datetime
import seaborn as sns
from matplotlib import pyplot as plt
from seaborn.axisgrid import FacetGrid

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

# curs.execute('select * from "nathria_prog_padded";')
# df = pd.DataFrame(curs.fetchall())
# df.columns = [desc[0] for desc in curs.description]
# avg_df = df.groupby(['pull_num','boss_num'], as_index=False).mean()
# sd_df = df.groupby(['pull_num','boss_num'], as_index=False).std()

#%%
curs.execute('select * from "nathria_prog_avg";')
avg_df = pd.DataFrame(curs.fetchall())
avg_df.columns = [desc[0] for desc in curs.description]
curs.execute('select * from "nathria_prog_std";')
sd_df = pd.DataFrame(curs.fetchall())
sd_df.columns = [desc[0] for desc in curs.description]

g = sns.FacetGrid(avg_df, col = 'boss_num', col_wrap = 4, sharex=False, sharey=True)
g.map(sns.lineplot, 'pull_num','end_perc', color = 'red')

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

axes = g.axes.flatten()
for k, ax in enumerate(axes):
    ax.set_ylabel("Wipe Percent")
    ax.set_xlabel("Pull Number")
    ax.set_title(boss_names[k])
    ax.set(ylim = (0, 100))
plt.tight_layout()
plt.savefig('avg_line_plot.pdf')  
#%% Pull Histogram

curs.execute('select MAX(pull_num), guild_name, boss_num, name from "nathria_prog" group by guild_name, boss_num, name;')
test = pd.DataFrame(curs.fetchall())
test.columns = [desc[0] for desc in curs.description]
test = test.rename(columns = {'max': 'pull_num'}).query('pull_num > 5')

# g = sns.FacetGrid(test, col = 'boss_num', col_wrap = 4, sharex = False, sharey = False)
# g.map(sns.histplot, 'pull_num')

# for k, ax in enumerate(g.axes.flatten()):
#     ax.set_ylabel('Guild Count')
#     ax.set_xlabel('Pull Number')
#     ax.set_title(boss_names[k])
# plt.tight_layout()
# plt.savefig('pull_hist.pdf')

import plotly.express as px
import plotly.graph_objects as go
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

fig = px.histogram(test, x = 'pull_num', facet_col = 'name', facet_col_wrap = 2,
    labels = {'pull_num': 'Pull Number',
              'name': ''},
    facet_col_spacing=0.1,
    facet_row_spacing=0.1,
    category_orders={'name': list(np.array(boss_names)[np.unique(test['boss_num']).astype(int)])},
    )

fig.add_trace(
    go.Scatter(
        x=[2, 4],
        y=[4, 8],
        mode="lines",
        line=go.scatter.Line(color="gray"),
        showlegend=False)
)


fig.update_layout(
    template = 'plotly_dark',
    plot_bgcolor = 'rgba(34,34,34,255)',
    paper_bgcolor = 'rgba(34,34,34,255)',
    autosize=True,
    # width=1500,
    height=np.ceil(10/2)*200,
    margin=dict(
        l=150,
        r=150,
        b=30,
        t=30,
        pad=4
    ),
    transition_duration = 500
)
fig.update_xaxes(matches = None)
fig.update_yaxes(matches = None)
fig.for_each_xaxis(lambda xaxis: xaxis.update(showticklabels=True))
fig.for_each_xaxis(lambda xaxis: xaxis.update(title = 'Kill Pull Number'))
fig.for_each_yaxis(lambda yaxis: yaxis.update(title = '# of Guilds'))
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig.show()

#%% Progression Time

curs.execute('select * from "nathria_guild_bossprog_hours";')
test = pd.DataFrame(curs.fetchall())
test.columns = [desc[0] for desc in curs.description]
test = test.query('prog_time > .5')

def filter_df(df, metric):
    new_df = pd.DataFrame()
    for boss_num in np.unique(df['boss_num']):
        boss_df = df.query('boss_num == '+str(boss_num))
        upper = np.quantile(boss_df[metric],.95)
        lower = np.quantile(boss_df[metric],.05)
        new_df = new_df.append(boss_df.query(str(metric)+ ' < '+str(upper)).query(str(metric)+ ' > '+str(lower)))
    return new_df

test = filter_df(test.copy(deep = True), 'prog_time')

g = sns.FacetGrid(test, col = 'boss_num', col_wrap = 4, sharex = False, sharey = False)
g.map(sns.histplot, 'prog_time')

for k, ax in enumerate(g.axes.flatten()):
    ax.set_ylabel('Guild Count')
    ax.set_xlabel('Progression Time (hrs)')
    ax.set_title(boss_names[k])
plt.tight_layout()
plt.savefig('prog_hours_hist.pdf')

import plotly.express as px
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

fig = px.histogram(test, x = 'prog_time', facet_col = 'name', facet_col_wrap = 2,
    labels = {'prog_time': 'Pull Number',
              'name': '',
              'title': 'Progression Time'},
    facet_col_spacing=0.1,
    facet_row_spacing=0.1,
    category_orders={'name': list(np.array(boss_names)[np.unique(test['boss_num']).astype(int)])},
    )

fig.update_layout(
    template = 'plotly_dark',
    plot_bgcolor = 'rgba(34,34,34,255)',
    paper_bgcolor = 'rgba(34,34,34,255)',
    autosize=True,
    # width=1500,
    height=np.ceil(10/2)*200,
    margin=dict(
        l=150,
        r=150,
        b=30,
        t=30,
        pad=4
    ),
    transition_duration = 500
)
fig.update_xaxes(matches = None)
fig.update_yaxes(matches = None)
fig.for_each_xaxis(lambda xaxis: xaxis.update(showticklabels=True))
fig.for_each_xaxis(lambda xaxis: xaxis.update(title = 'Progression Time (Hours)'))
fig.for_each_yaxis(lambda yaxis: yaxis.update(title = '# of Guilds'))
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig.show()

# %% Aggregating the data
curs.execute('select * from "nathria_prog";')
allpulls = pd.DataFrame(curs.fetchall())
allpulls.columns = [desc[0] for desc in curs.description]

temp_frame = pd.DataFrame()
for gn in np.unique(allpulls['guildnum']):
    one_guild = allpulls.query('guild_num == gn')
