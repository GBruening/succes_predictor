# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
#%%
import dash
import dash_bootstrap_components as dbc
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output

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


if 'conn' in locals():
    conn.close()
engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
curs = conn.cursor()

#%%
@app.callback(
    Output('single_guild_graph', 'figure'),
    Input('guild_name', 'value'),
    Input('prog_or_all', 'value')
)
def update_fig(guild_name, prog_or_all):
        
    # curs.execute('select distinct guild_name from nathria_prog')
    # guilds = [item[0] for item in curs.fetchall()]

    if prog_or_all == 'prog_only_pulls':
        curs.execute("select * from nathria_prog where guild_name = '" + str(guild_name)+"'")
    elif prog_or_all == 'all_pulls':
        curs.execute("select * from nathria_prog_allpulls where guild_name = '" + str(guild_name)+"'")

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
    fig.update_xaxes(matches = None)
    fig.for_each_xaxis(lambda xaxis: xaxis.update(showticklabels=True))
    fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fig.update_layout(
        template = 'plotly_dark',
        # plot_bgcolor = 'rgba(34,34,34,255)',
        # paper_bgcolor = 'rgba(34,34,34,255)',
        plot_bgcolor = 'rgba(0,0,0,255)',
        paper_bgcolor = 'rgba(0,0,0,255)',
        autosize=True,
        # width=1500,
        height=np.ceil(n_bosses/2)*300,
        margin=dict(
            l=150,
            r=150,
            b=30,
            t=60,
            pad=4
        ),
        transition_duration = 500,
        font = dict(size = 18)
    )
    return fig

# @app.callback(
#     Output(component_id='my-output', component_property='children'),
#     Input(component_id='guild_name', component_property='value')
# )
# def update_output_div(guild_name):
#     if 'conn' in locals():
#         conn.close()
#     engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
#     conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
#     curs = conn.cursor()

#     curs.execute('select distinct guild_name from nathria_prog')
#     guilds = [item[0] for item in curs.fetchall()]
#     # return 'Output: {}'.format(str(guilds[int(guild_num)]))
#     return 'Output: {}'.format(str(guild_name))

#%% Make App
app.layout = html.Div(children=[
    html.H1('Castle Nathria Pull Data', style={'backgroundColor':'black'}),
    html.Div([
        "Choose guild: ",
        dcc.Dropdown(id = 'guild_name',
                     options = [{'label': name, 'value': name} for k, name in enumerate(sorted(guilds))],
                     value = 'Dinosaur Cowboys',
                     style = {'color': 'black',
                              'width': '300px'})
    ]),
    html.Div([
       "All pulls or Progression Pulls?",
        dcc.RadioItems(options=[
            {'label': 'All Pulls', 'value': 'all_pulls'},
            {'label': 'Progression Only', 'value': 'prog_only_pulls'}
        ],
        id = 'prog_or_all',
        value = 'prog_only_pulls',
        labelStyle={'display': 'flex'}
        )
    ]),
    html.Br(style={'backgroundColor':'black'}),
    # html.Div(id='my-output'),
    dcc.Graph(
        id='single_guild_graph'
    )
    
], style={'backgroundColor':'black'})

if __name__ == '__main__':
    app.run_server(debug=True)

#%%

def make_agg_data_groupcomp(df):

    df = smalldf.copy(deep = True)
    n_pulls = len(df.unique_id.unique())

    df['test'] = df[df.columns[1:4]].apply(
        lambda x: ', '.join(x.dropna().astype(str)),
        axis=1
    )

    temp_df = df.groupby(['unique_id','test']).\
        size().unstack(fill_value=0).stack().reset_index(name='counts')

    temp_df['p_class'] = temp_df[temp_df.columns[1]].apply(
        lambda x: re.findall('(.*),\s(.*),\s(.*)', str(x))[0][0]
    )
    temp_df['spec'] = temp_df[temp_df.columns[1]].apply(
        lambda x: re.findall('(.*),\s(.*),\s(.*)', str(x))[0][1]
    )
    temp_df['role'] = temp_df[temp_df.columns[1]].apply(
        lambda x: re.findall('(.*),\s(.*),\s(.*)', str(x))[0][2]
    )

    temp_df.groupby(['p_class','spec','role']).size().reset_index().dropna()

    df.groupby(['p_class', 'spec', 'role']).\
        size().\
        reset_index(name='counts')


    # avg_comp = temp_df.groupby(['test']).mean().reset_index().dropna().iloc[:,0:2].rename(columns={'p_class': 'mean_val'})
    # std_comp = temp_df.groupby(['test']).std().reset_index().dropna().iloc[:,0:2].rename(columns={'p_class': 'std_val'})


    # df = pd.merge(avg_comp, std_comp, on=['p_class', 'spec'], how='inner').\
    #     rename(columns={'role_x': 'role'}).query('role == "dps"')

    # df = df.reindex(columns=['p_class', 'spec', 'role', 'mean_val','std_val'])

    return df