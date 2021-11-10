# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
#%%
import pandas as pd
import pickle
import joblib

import dash
import dash_bootstrap_components as dbc
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.express as px
import plotly.graph_objects as go

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])

#%% Create Data
import numpy as np
import json
import os
import time
from datetime import datetime

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

curs.execute('select distinct guild_name from nathria_prog')
guilds = [item[0] for item in curs.fetchall()]

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

#%%
specific_boss = boss_names[0]
guild_name = 'Dinosaur Cowboys'
prog_or_all = 'all_pulls'

# curs.execute('select distinct guild_name from nathria_prog')
# guilds = [item[0] for item in curs.fetchall()]

specific_boss = specific_boss.replace("'", "''")
# curs.execute(f"select * from nathria_kill_comps where name = '{specific_boss}';")

if prog_or_all == 'prog_only_pulls':
    curs.execute(f"select * from nathria_prog where guild_name = '{guild_name}' and name = '{specific_boss}'")
elif prog_or_all == 'all_pulls':
    curs.execute(f"select * from nathria_prog_allpulls where guild_name = '{guild_name}' and name = '{specific_boss}'")

# curs.execute("select * from nathria_prog where guild_name = '" + str(guilds[int(guild_num)])+"'")
pulls = pd.DataFrame(curs.fetchall())
pulls.columns = [desc[0] for desc in curs.description]
newdf = pulls.sort_values(by = 'boss_num')
n_bosses = len(np.unique(pulls['boss_num']))
# # Fixing Data frames cause I don't know why
# newdf = pd.DataFrame()
# for k in np.unique(pulls['boss_num']):
#     bossdf = pulls.query('boss_num == ' + str(k))
#     did_kill = len(bossdf.query('kill == 1')['pull_num']) > 0
#     if did_kill:
#         last_pull = min(bossdf.query('kill == 1')['pull_num'])
#     else: 
#         last_pull = len(bossdf)

#     newdf = newdf.append(bossdf.query('pull_num <= '+str(last_pull)))
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

fig = px.scatter(newdf, x = 'pull_num', y = 'end_perc', facet_col = 'name', facet_col_wrap=2,
    labels = {"pull_num": 'Pull Number',
            "end_perc": 'Wipe Percent (%)',
            "name": ''},
    category_orders={'name': list(np.array(boss_names)[np.unique(newdf['boss_num']).astype(int)])},
    facet_col_spacing=0.06)#, title = str(guild_name))
fig.update_traces(hovertemplate = 'Pull %{x}<br>%{y:.2f}% Wipe')
fig.update_xaxes(matches = None)
fig.for_each_xaxis(lambda xaxis: xaxis.update(showticklabels=True))
fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
fig.for_each_xaxis(lambda xaxis: xaxis.update(title = 'Pull Number'))
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

fig.update_layout(
    template = 'plotly_dark',
    # plot_bgcolor = 'rgba(34,34,34,255)',
    # paper_bgcolor = 'rgba(34,34,34,255)',
    plot_bgcolor = 'rgba(0,0,0,255)',
    paper_bgcolor = 'rgba(0,0,0,255)',
    autosize=True,
    width=500,
    height=np.ceil(n_bosses/2)*300,
    margin=dict(
        l=100,
        r=40,
        b=30,
        t=30,
        pad=2
    ),
    transition_duration = 500,
    font = dict(size = 14)
)

#%%
filename = f'{boss_str}_mod.pickle'
clf = joblib.load(filename)

def listify_pulls(end_perc):
    pull_list = []

    n_fights = 10
    end_perc

    pulls = [100]*n_fights
    for k in range(len(end_perc)-1):
        if k == 0:
            pass
        else:
            pulls.pop(0)
            pulls.append(end_perc[k])
        pull_list.append(pulls.copy())
    return pull_list

pulls = listify_pulls(list(newdf.sort_values(by = ['pull_num'])['end_perc']))

s_prob = [item[1] for item in clf.predict_proba(pulls)]

fig2 = fig
fig2.add_trace(
    go.Scatter(x = sorted(newdf['pull_num']), 
               y = np.array(s_prob)*100,
               showlegend = False,
               name = '',
               hovertemplate = 'Win Prob<br>%{y:.2f}'),
    row = 1,
    col = 1,
)
fig2.update_layout(hovermode = 'x unified')

#%%
@app.callback(
    Output('single_guild_graph', 'figure'),
    Input('guild_name', 'value'),
    Input('prog_or_all', 'value'),
    Input('specific_boss', 'value')
)
def update_fig(guild_name, prog_or_all, specific_boss):
    return fig
