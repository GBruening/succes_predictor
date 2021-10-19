# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
#%%
import dash
import dash_bootstrap_components as dbc
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# app = Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])

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

#%%
@app.callback(
    Output('single_guild_graph', 'figure'),
    Input('specific_boss', 'value'),
)
def update_fig(specific_boss):
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
    specific_boss = specific_boss.replace("'", "''")
    
    fig = make_subplots(rows=2, cols=2,
                        vertical_spacing = 0.25)

    # Pull Count Plotting
    pull_count_query = \
        f"\
            select name, pull_num, average_item_level from max_pull_count_small \
            where name = '{specific_boss}' and kill = 'True';\
        "
    curs.execute(pull_count_query)
    pull_count = pd.DataFrame(curs.fetchall())
    pull_count.columns = [desc[0] for desc in curs.description]
    pull_count = pull_count.rename(columns = {'max': 'pull_num'}).query('pull_num > 5')
    pull_count = add_boss_nums(pull_count)
    pull_count = filter_df(pull_count.copy(deep = True), 'pull_num')
    
    fig.append_trace(go.Histogram(
        x = pull_count['pull_num'], histnorm='probability',
        name = 'Pull Count',
        marker=dict(color = 'grey'),
    ), row=1, col=1)
    fig['layout']['xaxis']['title'] = 'Total Pull Count'
    fig['layout']['yaxis']['title'] = 'Proportion'
    fig.add_vline(
        x = np.median(pull_count['pull_num']),
            line_color = 'red',
        row = 1,
        col = 1
    )
    
    # Average Item Level Plotting
    fig.append_trace(go.Histogram(
        x = filter_df(pull_count.copy(deep = True), 'average_item_level')['average_item_level'], 
        histnorm='probability',
        name = 'Item Level',
        marker=dict(color = 'grey'),
    ), row=1, col=2)
    fig['layout']['xaxis2']['title'] = 'Average Group Item Level at Kill'
    fig['layout']['yaxis2']['title'] = 'Proportion'
    fig.add_vline(
        x = np.median(pull_count['average_item_level']),
            line_color = 'red',
        row = 1,
        col = 2
    )

    # Progression Time Plotting
    curs.execute(f"select boss_num, prog_time, name, guild_name \
        from nathria_guild_bossprog_hours \
        where name = '{specific_boss}' and prog_time > 0.5;")
    prog_hours = pd.DataFrame(curs.fetchall())
    prog_hours.columns = [desc[0] for desc in curs.description]
    prog_hours = add_boss_nums(prog_hours)
    prog_hours = filter_df(prog_hours.copy(deep = True), 'prog_time')
    # prog_hours = pd.read_csv('G://My Drive//succes_predictor//dash2//prog_hours.csv')
    # prog_hours = prog_hours.query(f'boss_num == {boss_num}')
    # fig = px.histogram(prog_hours, x = 'prog_time')
    fig.append_trace(go.Histogram(
        x = prog_hours['prog_time'], histnorm='probability',
        name = 'Progression Hours',
        marker=dict(color = 'grey'),
    ), row=2, col=1)
    fig['layout']['xaxis3']['title'] = 'Total Progression Time (Hours)<br>(Includes groups that have not killed boss)'
    fig['layout']['yaxis3']['title'] = 'Proportion'
    fig.add_vline(
        x = np.median(prog_hours['prog_time']),
            line_color = 'red',
        row = 2,
        col = 1
    )

    # Kill Dates
    kill_date_query = \
        f"\
            select name, (log_start + end_time)/1000 as kill_time \
            from max_pull_count_small \
            where name = '{specific_boss}' and kill = 'True';\
        "
    curs.execute(kill_date_query)
    kill_dates = pd.DataFrame(curs.fetchall())
    kill_dates.columns = [desc[0] for desc in curs.description]
    kill_dates['date'] = [datetime.datetime.fromtimestamp(item) for item in kill_dates['kill_time']]
    kill_dates = add_boss_nums(kill_dates)
    kill_dates = filter_df(kill_dates.copy(deep = True), 'kill_time')

    # n, bins, patches = plt.hist(kill_dates['kill_time'], 100, density=True, histtype='step',
    #                         cumulative=True, label='Empirical')
    n, bins = np.histogram(kill_dates['kill_time'], bins = 100, density = True)  
    dx = bins[1] - bins[0]
    n = np.cumsum(n)*dx

    new_kill_df = pd.DataFrame(data = {'n': n, 'kill_time': bins[0:-1]})
    new_kill_df['date'] = [datetime.datetime.fromtimestamp(item) for item in new_kill_df['kill_time']]

    fig.append_trace(go.Scatter(
        x = new_kill_df['date'],
        y = new_kill_df['n'],
        name = 'Kill Date',
        mode = 'lines',
        marker=dict(color = 'grey'),
    ), row=2, col=2)
    fig['layout']['xaxis4']['tickangle'] = -45
    fig['layout']['xaxis4']['title'] = 'Date of kill'
    fig['layout']['yaxis4']['title'] = 'Cumulative Density'
    # fig.add_vline(
    #     x = np.median(kill_dates['date']),
    #         line_color = 'red',
    #     row = 2,
    #     col = 2
    # )

    # Update the Figure
    fig.update_layout(
        template = 'plotly_dark',
        plot_bgcolor = 'rgba(0,0,0,255)',
        paper_bgcolor = 'rgba(0,0,0,255)',
        bargap = 0.1,
        autosize=True,
        # width=1500,
        # height=np.ceil(10/2)*200,
        height=600,
        margin=dict(
            l=100,
            r=100,
            b=50,
            t=30,
            pad=2
        ),
        transition_duration = 500,
        font = dict(size = 14),
        showlegend = False
    )

    # fig.update_xaxes(matches = None)
    # fig.update_yaxes(matches = None)
    # fig.for_each_xaxis(lambda xaxis: xaxis.update(showticklabels=True))
    # fig.for_each_xaxis(lambda xaxis: xaxis.update(title = 'Kill Pull Number'))
    # fig.for_each_yaxis(lambda yaxis: yaxis.update(title = '# of Guilds'))
    # fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    agg_plot = fig
    return agg_plot


@app.callback(
    Output('group_comp_plot', 'figure'),
    Input('specific_boss', 'value')
)
def make_comp_plot(specific_boss):
    specific_boss = specific_boss.replace("'", "''")
    curs.execute(f"select * from nathria_kill_comps where name = '{specific_boss}';")
    sql_df = pd.DataFrame(curs.fetchall())
    sql_df.columns = [desc[0] for desc in curs.description]

    df = sql_df
        
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
                hovertemplate = '%{text} %{x} <br> %{y:.2f} ± %{error_y:.2f}',
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
        # height=np.ceil(10/2)*200,
        height=400,
        width = 1000,
        margin=dict(
            l=100,
            r=100,
            b=50,
            t=30,
            pad=2
        ),
        autosize=True,
        transition_duration = 500,
        font = dict(size = 14),
        uniformtext_minsize=4, 
        uniformtext_mode='show',
        showlegend = False,
        title_text=f'Approximate group composition<br>for {specific_boss}', 
        title_x=0.5
    )
    comp_plot = fig
    return comp_plot


#%% Make App
app.layout = html.Div(children=[
    html.H1('Castle Nathria Pull Statistics', style={'backgroundColor':'black'}),
    html.Div([
        'Choose Boss',
        dcc.Dropdown(id = 'specific_boss',
                    options = [{'label': name, 'value': name} for k, name in enumerate(boss_names)],
                    value = boss_names[0],
                    style = {'color': 'black',
                            'width': '300px'})
    ]),
    html.Div([
        # html.Div([
        #     "Choose guild: ",
        #     dcc.Dropdown(id = 'guild_name',
        #                  options = [{'label': name, 'value': name} for k, name in enumerate(sorted(guilds))],
        #                  value = 'Dinosaur Cowboys',
        #                  style = {'color': 'black',
        #                           'width': '300px'})
        # ]),
        html.Br(style={'backgroundColor':'black'}),
        dcc.Graph(
            id='single_guild_graph'
        )
    ])
    ,
    html.Div([
        html.Br(style={'backgroundColor':'black'}),
        dcc.Graph(
            id = 'group_comp_plot'
        )
    ])    
], style={'backgroundColor':'black'})

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)

#%%