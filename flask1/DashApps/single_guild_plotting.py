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
import plotly.graph_objects as go

import joblib

import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])

#%% Create Data
import numpy as np
import json
import os
import time
from datetime import datetime

try:
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
except:
    print(f"Data base not found, using csv.")
    data = pd.read_csv(dname+'/../../Pulling data/nathria_prog_allpulls_small.csv')
    guilds = data['guild_name'].unique()

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
    Input('guild_name', 'value'),
    Input('prog_or_all', 'value'),
    Input('specific_boss', 'value')
)
def update_fig(guild_name, prog_or_all, specific_boss):
        
    # curs.execute('select distinct guild_name from nathria_prog')
    # guilds = [item[0] for item in curs.fetchall()]

    specific_boss = specific_boss.replace("'", "''")
    # curs.execute(f"select * from nathria_kill_comps where name = '{specific_boss}';")

    try:
        if prog_or_all == 'prog_only_pulls':
            curs.execute(f"select * from nathria_prog where guild_name = '{guild_name}' and name = '{specific_boss}'")
        elif prog_or_all == 'all_pulls':
            curs.execute(f"select * from nathria_prog_allpulls where guild_name = '{guild_name}' and name = '{specific_boss}'")

        # curs.execute("select * from nathria_prog where guild_name = '" + str(guilds[int(guild_num)])+"'")
        pulls = pd.DataFrame(curs.fetchall())
        pulls.columns = [desc[0] for desc in curs.description]
    except:
        print(f"Data base not found, using csv.")
        if prog_or_all == 'prog_only_pulls':
            data = pd.read_csv(dname+'/../../Pulling data/nathria_prog_small.csv')
            guilds = data['guild_name'].unique()

            pulls = data.query(f"guild_name == '{guild_name}' and name == '{specific_boss}'")
        elif prog_or_all == 'all_pulls':
            data = pd.read_csv(dname+'/../../Pulling data/nathria_prog_allpulls_small.csv')
            guilds = data['guild_name'].unique()
            
            pulls = data.query(f"guild_name == '{guild_name}' and name == '{specific_boss}'")



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

    # fig = px.scatter(newdf, x = 'pull_num', y = 'end_perc', 
    #     facet_col = 'name', 
    #     facet_col_wrap=2,
    #     labels = {"pull_num": 'Pull Number',
    #             "end_perc": 'Wipe Percent (%)',
    #             "name": 'Wipe Percentage (0 = Kill)'},
    #     category_orders={'name': list(np.array(boss_names)[np.unique(newdf['boss_num']).astype(int)])},
    #     facet_col_spacing=0.06)#, title = str(guild_name))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x = newdf['pull_num'], 
        y = newdf['end_perc'],
        name = 'Wipe Percentage (0 = Kill)',
        mode = 'markers')
        )
    fig.update_yaxes(title = 'Wipe or Success Probability (%)', range = [-3, 100])
    fig.update_traces(hovertemplate = 'Pull %{x}<br>%{y:.2f}% Wipe')
    fig.update_xaxes(matches = None)
    fig.for_each_xaxis(lambda xaxis: xaxis.update(showticklabels=True))
    fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
    fig.for_each_xaxis(lambda xaxis: xaxis.update(title = 'Pull Number'))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    try:
        model_specific_boss = specific_boss.replace(' ','_')
        filename = f'{model_specific_boss}_mod.pickle'
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

        fig = fig
        fig.add_trace(
            go.Scatter(x = sorted(newdf['pull_num']), 
                    y = np.array(s_prob)*100,
                    marker = {'size': 0,
                            'opacity': 0},
                    # showlegend = False,
                    name = 'Kill Probability<br>on next pull',
                    # hovertemplate = 'Win Prob<br>on next pull<br>%{y:.2f}%'),
                    hovertemplate = '%{y:.2f}%'),
            # row = 1,
            # col = 1,
        )
    except:
        pass
    
    fig.update_layout(hovermode = 'x')
    fig.update_layout(
        template = 'plotly_dark',
        # plot_bgcolor = 'rgba(34,34,34,255)',
        # paper_bgcolor = 'rgba(34,34,34,255)',
        plot_bgcolor = 'rgba(0,0,0,255)',
        paper_bgcolor = 'rgba(0,0,0,255)',
        autosize=True,
        width=1000,
        height=np.ceil(n_bosses/2)*400,
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
        value = 'all_pulls',
        labelStyle={'display': 'flex'}
        )
    ]),
    html.Div([
        'Choose Boss',
        dcc.Dropdown(id = 'specific_boss',
                    options = [{'label': name, 'value': name} for k, name in enumerate(boss_names)],
                    value = boss_names[0],
                    style = {'color': 'black',
                            'width': '300px'})
    ]),
    html.Br(style={'backgroundColor':'black'}),
    # html.Div(id='my-output'),
    dcc.Graph(
        id='single_guild_graph', style={'backgroundColor':'black'}
    ),
   html.Br(),   
   html.Br(),   
   html.Br(),
    
], style={'backgroundColor':'black'})

if __name__ == '__main__':
    app.run_server(debug=False, port=8051)
