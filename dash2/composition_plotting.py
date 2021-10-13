
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np
import json
import os
import time
import datetime

from sqlalchemy import create_engine
import psycopg2

def add_boss_nums(df):

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

def filter_df(df, metric):
    new_df = pd.DataFrame()
    for boss_num in np.unique(df['boss_num']):
        boss_df = df.query('boss_num == '+str(boss_num))
        upper = np.quantile(boss_df[metric],.99)
        lower = np.quantile(boss_df[metric],.01)
        new_df = new_df.append(boss_df.query(str(metric)+ ' < '+str(upper)).query(str(metric)+ ' > '+str(lower)))
    return new_df

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# app = Dash(__name__, external_stylesheets=external_stylesheets)
# app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])

#%% Create Data
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

curs.execute('select distinct guild_name from nathria_prog')
guilds = [item[0] for item in curs.fetchall()]
# guilds = ['Dinosaur Cowboys']

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


kills_query = \
    f"\
        select * from max_pull_count_small \
        where name = '{specific_boss}' and kill = 'True';\
    "
curs.execute(kills_query)
kills_query = pd.DataFrame(curs.fetchall())
kills_query.columns = [desc[0] for desc in curs.description]

specific_boss = boss_names[0]
if 'conn' in locals():
    conn.close()
engine = create_engine('postgresql://postgres:postgres@192.168.0.6:5432/nathria_prog')
conn = psycopg2.connect('host=192.168.0.6 dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()
    
specific_boss = boss_names[-1]


def make_comp_plot(specific_boss):
    
    curs.execute(f"select kill_df.unique_id, class as p_class, spec, role, \
        ilvl, covenant, boss_name \
        from nathria_prog_v2_players as players \
        join \
            (select * from max_pull_count_small \
            where name = '{specific_boss}' and kill = 'True') as kill_df \
        on players.unique_id = kill_df.unique_id;")
    test = pd.DataFrame(curs.fetchall())
    test.columns = [desc[0] for desc in curs.description]

    n_pulls = len(test.unique_id.unique())
    test2 = test.groupby(['unique_id','p_class', 'spec', 'role']).\
        size().\
        reset_index(name='counts')
        
    avg_comp = test2.\
        groupby(['p_class','spec','role']).\
        mean().reset_index().dropna().\
        rename(columns={'counts': 'mean_val'})
    std_comp = test2.\
        groupby(['p_class','spec','role']).\
        std().reset_index().dropna().\
        rename(columns={'counts': 'std_val'})
    counts_comp = test2.\
        groupby(['p_class','role','spec']).\
        sum().reset_index().dropna()

    comb_df = pd.merge(avg_comp, std_comp, on=['p_class', 'spec'], how='inner').\
        rename(columns={'role_x': 'role'})
        
    colors = {'DeathKnight': '#D62728',
            'DemonHunter': '#750D86',
            'Druid': '#F58518',
            'Hunter': '#54A24B',
            'Mage': '#17BECF',
            'Monk': '#22FFA7',
            'Paladin': '#FF97FF',
            'Priest': '#E2E2E2',
            'Rogue': '#EECA3B',
            'Shaman': '#3366CC',
            'Warlock': '#636EFA',
            'Warrior': '#8C564B'}

    bars = []
    for p_class in df['p_class'].unique():
        class_df = df.query(f"p_class == '{p_class}'")
        spec_count = 0
        specs = class_df['spec'].unique()
        if len(specs) == 2:
            offsets = [1,3]
        elif len(specs) == 1:
            offsets = [2]
        else:
            offsets = [0,2,4]
        for spec in specs:
            spec_df = class_df.query(f"spec == '{spec}'")
            bars.append(go.Bar(
                x = spec_df.p_class,
                y = spec_df.mean_val,
                width = .25,
                error_y=dict(
                    type='data', 
                    array=[spec_df.std_val],
                    thickness=0.75),
                text = spec_df.spec,
                offsetgroup = spec_count,
                showlegend = False,
                marker = {'color': colors[p_class]}))
            # bars[-1].hoverlabel = spec
            spec_count += 1
    fig = go.FigureWidget(data=bars)
    fig['layout']['xaxis']['tickangle'] = -30
    fig['layout']['xaxis']['title'] = 'Player Class'
    fig['layout']['yaxis']['title'] = 'Average number of class/spec<br>in kill group (mean ± SD).'
    fig.update_traces(textposition='outside')
    fig.update_layout(
        template = 'plotly_dark',
        plot_bgcolor = 'rgba(0,0,0,255)',
        paper_bgcolor = 'rgba(0,0,0,255)',
        autosize=True,
        transition_duration = 500,
        font = dict(size = 12),
        uniformtext_minsize=4, 
        uniformtext_mode='show',
        showlegend = False,
        title_text=f'Approximate group composition<br>for {specific_boss}', 
        title_x=0.5
    )
    return fig

testdf = comb_df.query("role == 'dps'").copy(deep=True)
fig = make_comp_plot(testdf)
# CURRENTLY INCORRECT BECAUSE OF HOW OFTEN THINGS SHOW UP

#%%