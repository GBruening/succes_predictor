
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
import regex as re

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


specific_boss = boss_names[-1]
kills_query = \
    f"\
        select * from max_pull_count_small \
        where name = '{specific_boss}' and kill = 'True';\
    "
curs.execute(kills_query)
kills_query = pd.DataFrame(curs.fetchall())
kills_query.columns = [desc[0] for desc in curs.description]

if 'conn' in locals():
    conn.close()
try:
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
    conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
except:
    engine = create_engine('postgresql://postgres:postgres@192.168.0.6:5432/nathria_prog')
    conn = psycopg2.connect('host=192.168.0.6 dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()

def make_agg_data_groupcomp(specific_boss):  
    specific_boss = specific_boss.replace("'", "''")
    
    curs.execute(f"select kill_df.unique_id, class as p_class, spec, role, \
        ilvl, covenant, boss_name \
        from nathria_prog_v2_players as players \
        join \
            (select * from max_pull_count_small \
            where name = '{specific_boss}' and kill = 'True') as kill_df \
        on players.unique_id = kill_df.unique_id;")
    sql_df = pd.DataFrame(curs.fetchall())
    sql_df.columns = [desc[0] for desc in curs.description]

    n_pulls = len(sql_df.unique_id.unique())
      
    df = sql_df
    df = df.dropna(subset = ['p_class','spec','role'])

    df['test'] = df[df.columns[1:4]].apply(
        lambda x: ', '.join(x.dropna().astype(str)),
        axis=1
    )

    temp_df = df.groupby(['unique_id','test']).\
        size().unstack(fill_value=0).stack().reset_index(name='counts')

    test = []
    for x in temp_df[temp_df.columns[1]]:
        test.append(re.findall('(.*),\s(.*),\s(.*)', str(x))[0][0])
    temp_df['p_class'] = temp_df[temp_df.columns[1]].apply(
        lambda x: re.findall('(.*),\s(.*),\s(.*)', str(x))[0][0]
    )
    temp_df['spec'] = temp_df[temp_df.columns[1]].apply(
        lambda x: re.findall('(.*),\s(.*),\s(.*)', str(x))[0][1]
    )
    temp_df['role'] = temp_df[temp_df.columns[1]].apply(
        lambda x: re.findall('(.*),\s(.*),\s(.*)', str(x))[0][2]
    )

    avg_comp = temp_df.groupby(['p_class','spec','role']).mean().reset_index().dropna().rename(columns={'counts': 'mean_val'})
    std_comp = temp_df.groupby(['p_class','spec','role']).std().reset_index().dropna().rename(columns={'counts': 'std_val'})
    std_comp['std_val'] = std_comp['std_val']/np.sqrt(n_pulls)

    df = pd.merge(avg_comp, std_comp, on=['p_class', 'spec'], how='inner').\
        rename(columns={'role_x': 'role'})

    df = df.reindex(columns=['p_class', 'spec', 'role', 'mean_val','std_val'])
    df['n_pulls'] = n_pulls

    return df

def make_comp_plot(specific_boss):
    df = make_agg_data_groupcomp(specific_boss)

    # df = df.groupby(['p_class', 'spec', 'role']).\
    #     size().\
    #     reset_index(name='counts')

    # avg_comp = df.\
    #     groupby(['p_class','spec','role']).\
    #     mean().reset_index().dropna().\
    #     rename(columns={'counts': 'mean_val'})
    # std_comp = df.\
    #     groupby(['p_class','spec','role']).\
    #     std().reset_index().dropna().\
    #     rename(columns={'counts': 'std_val'})
    # counts_comp = df.\
    #     groupby(['p_class','role','spec']).\
    #     sum().reset_index().dropna()
    # counts_comp.counts = counts_comp.counts/n_pulls
    # # df = pd.merge(avg_comp, std_comp, on=['p_class', 'spec'], how='inner').\
    # #     rename(columns={'role_x': 'role'}).query('role == "dps"')
        
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
                # y = spec_df.counts,
                width = .15,
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

#%%
# testdf = comb_df.query("role == 'dps'").copy(deep=True)
fig = make_comp_plot(specific_boss)
# CURRENTLY INCORRECT BECAUSE OF HOW OFTEN THINGS SHOW UP

subplots = [[1,1],
            [1,2],
            [2,1],
            [2,2],
            [3,1],
            [3,2],
            [4,1],
            [4,2],
            [5,1],
            [5,2]]
bosses_to_plot = [name for name in np.array(boss_names)[0:1]]
fig2 = make_subplots(rows=int(np.ceil(len(bosses_to_plot)/2)), cols=2,
        vertical_spacing = 0.25,
        subplot_titles = bosses_to_plot)

# fig2.append_trace(fig, row=1, col=1)

for k, boss in enumerate(bosses_to_plot):
    print(k)
    fig = make_comp_plot(boss)
    print(subplots[k][0], subplots[k][1])
    for item in fig.data:
        fig2.append_trace(item, row=subplots[k][0], col=subplots[k][1])

fig2.for_each_xaxis(lambda xaxis: xaxis.update(title = 'Player Class', tickangle = -20))
fig2.for_each_yaxis(lambda yaxis: yaxis.update(title = '# of Class in Group.'))

fig2.update_layout(
    width = 900,
    height = 300*len(bosses_to_plot)/2,
    template = 'plotly_dark',
    plot_bgcolor = 'rgba(0,0,0,255)',
    paper_bgcolor = 'rgba(0,0,0,255)',
    # autosize=True,
    transition_duration = 500,
    font = dict(size = 9),
    uniformtext_minsize=4, 
    uniformtext_mode='show',
    showlegend = False,
    title_text=f'Approximate group composition', 
    title_x=0.5
)


#%% Add stuff to Sql


# playerdf.to_sql('nathria_prog_v2_players', engine, if_exists='append')

for specific_boss in boss_names:
    print(f'Making sql for group comp: {specific_boss}')
    df = make_agg_data_groupcomp(specific_boss)
    df['name'] = specific_boss
    df.to_sql('nathria_kill_comps', engine, if_exists='append')

# %%
