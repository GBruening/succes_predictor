# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
#%%
import dash
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

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

#%%
@app.callback(
    Output('single_guild_graph', 'figure'),
    Input('guild_name', 'value')
)
def update_fig(guild_name):
        
    if 'conn' in locals():
        conn.close()
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
    conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
    curs = conn.cursor()
    curs.execute('select distinct guild_name from nathria_prog')
    guilds = [item[0] for item in curs.fetchall()]

    curs.execute("select * from nathria_prog where guild_name = '" + str(guild_name)+"'")
    # curs.execute("select * from nathria_prog where guild_name = '" + str(guilds[int(guild_num)])+"'")
    pulls = pd.DataFrame(curs.fetchall())
    pulls.columns = [desc[0] for desc in curs.description]
    newdf = pulls.sort_values(by = 'boss_num')
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
        facet_col_spacing=0.06,
        title = str(guild_name))
    fig.update_xaxes(matches = None)
    fig.for_each_xaxis(lambda xaxis: xaxis.update(showticklabels=True))
    fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fig.update_layout(
        template = 'plotly_dark',
        autosize=False,
        width=1500,
        height=1500,
        margin=dict(
            l=70,
            r=70,
            b=30,
            t=30,
            pad=4
        ),
        transition_duration = 500
    )
    return fig

@app.callback(
    Output(component_id='my-output', component_property='children'),
    Input(component_id='guild_name', component_property='value')
)
def update_output_div(guild_name):
    if 'conn' in locals():
        conn.close()
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/nathria_prog')
    conn = psycopg2.connect('host='+server+' dbname='+database+' user='+username+' password='+password)
    curs = conn.cursor()

    curs.execute('select distinct guild_name from nathria_prog')
    guilds = [item[0] for item in curs.fetchall()]
    # return 'Output: {}'.format(str(guilds[int(guild_num)]))
    return 'Output: {}'.format(str(guild_name))
#%% Make App
app.layout = html.Div(children=[
    html.H1('Plot 1'),
    html.H6("Change the value in the text box to see callbacks in action!"),
    # html.Div([
    #     "Input: ",
    #     # dcc.Input(id='guild_num', placeholder = 'Enter a guild number...', value='2748', type='text')
    #     dcc.Textarea(id = 'guild_name',
    #                  placeholder = 'Enter a guild name...',
    #                  value = 'Dinosaur Cowboys',
    #                  style = {'width': '100'})
    # ]),
    html.Div([
        "Input2: ",
        # dcc.Input(id='guild_num', placeholder = 'Enter a guild number...', value='2748', type='text')
        dcc.Dropdown(id = 'guild_name',
                     options = [{'label': name, 'value': name} for k, name in enumerate(guilds)],
                     value = 'Dinosaur Cowboys')
    ]),
    html.Br(),
    html.Div(id='my-output'),

    html.Div(children='''
        Testing plotting with dash.
    '''),

    dcc.Graph(
        id='single_guild_graph'
    )
    
])

if __name__ == '__main__':
    app.run_server(debug=True)