# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
#%%
import dash
import dash_bootstrap_components as dbc
from dash import Dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output
import plotly.graph_objects as go

import joblib
import regex as re
    
#%% Functions
def filter_df(df_filter, metric):
    new_df_filt = pd.DataFrame()
    for boss_num in np.unique(df_filter['boss_num']):
        boss_df = df_filter.query('boss_num == '+str(boss_num))
        upper = np.quantile(boss_df[metric],.99)
        lower = np.quantile(boss_df[metric],.01)
        new_df_filt = new_df_filt.append(boss_df.query(str(metric)+ ' < '+str(upper)).query(str(metric)+ ' > '+str(lower)))
    return new_df_filt

def listify_pulls(end_perc2):
    pull_list = []

    n_fights = 10

    pulls_ml = [100]*n_fights
    for k in range(len(end_perc2)-1):
        if k == 0:
            pass
        else:
            pulls_ml.pop(0)
            pulls_ml.append(end_perc2[k])
        pull_list.append(pulls_ml.copy())
    return pull_list

def rm_repeat_boss(df):
    df = df.sort_values(by = ['fight_start_time'])
    temp_df = pd.DataFrame()
    temp_df = temp_df.append(df.iloc[0])

    last_start = df.iloc[0]['fight_start_time']
    last_perc = df.iloc[0]['boss_perc']
    for index, row in df[1:].iterrows():
        if abs(row['fight_start_time'] - last_start)/1000 > 30:
            if row['boss_perc'] > 0 and row['boss_perc'] != last_perc:
                temp_df = temp_df.append(row)
                last_start = row['fight_start_time']
                last_perc = row['boss_perc']
            elif row['boss_perc'] == 0:
                temp_df = temp_df.append(row)
                last_start = row['fight_start_time']
                last_perc = row['boss_perc']

    temp_df = temp_df.reset_index(drop = True)
    temp_df['pull_num'] = temp_df.index+1
    return temp_df


#%% Create Data
import numpy as np
import json
import os
import time
from datetime import datetime

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)

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
            
def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix="/SingleGuild_app/",
        external_stylesheets=[
            "/static/dist/css/styles.css",
            "https://fonts.googleapis.com/css?family=Lato",
        ],
    )
    # external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    # dash_app.server = dash.Dash(external_stylesheets=[dbc.themes.DARKLY])

    pulls_all = pd.read_csv(dname+'/nathria_prog_allpulls_small.csv')

    guilds = pulls_all['guild_name'].unique()

    #%%
    @dash_app.callback(
        Output('single_guild_graph', 'figure'),
        Input('guild_name', 'value'),
        Input('specific_boss', 'value')
    )
    def update_fig(guild_name, specific_boss):
        
        specific_boss = specific_boss.replace("'", "\\'")

        pulls = pulls_all.query(f"guild_name == '{guild_name}'").query(f"name == '{specific_boss}'")
        newdf = pulls.sort_values(by = 'boss_num').sort_values(by = 'pull_num')
        n_bosses = len(np.unique(pulls['boss_num']))
        
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

        # try:
        from sklearn.base import BaseEstimator, RegressorMixin, TransformerMixin
        class pull_encoder(BaseEstimator, TransformerMixin):
            def fit(self, X, y = None):
                return self
            
            def transform(self, X):
                if isinstance(X, list):
                    return X
                else:
                    return [ast.literal_eval(item) for item in list(X['pulls'])]
                    
        model_specific_boss = specific_boss.replace(' ','_').replace("\\'",'')
        filename = dname+f'//{model_specific_boss}_mod.pickle'
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
        )
        
        fig.update_layout(hovermode = 'x')
        fig.update_layout(
            template = 'plotly_dark',
            plot_bgcolor = '#222222',
            paper_bgcolor = '#222222',
            # plot_bgcolor = 'rgba(0,0,0,255)',
            # paper_bgcolor = 'rgba(0,0,0,255)',
            autosize=True,
            # width=1000,
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

    pull_df_players = pd.read_csv(dname+'/only_first_kill_players.csv')

    @dash_app.callback(
        Output('single_guild_comp', 'figure'),
        Input('guild_name', 'value'),
        Input('specific_boss', 'value')
    )
    def create_single_guild_comp(guild_name, specific_boss):
        # specific_boss = boss_names[1]
        specific_boss = specific_boss.replace("'", "\\'")
        player_df = pull_df_players.query(f"guild_name == '{guild_name}'").query(f"name == '{specific_boss}'")
            
        player_df['test'] = player_df[player_df.columns[18:21]].apply(
            lambda x: ', '.join(x.dropna().astype(str)),
            axis=1
        )

        temp_df = player_df.groupby(['unique_id','test']).\
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
        df = temp_df.copy(deep = True)

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
            if p_class not in colors.keys():
                continue
            class_df = df.query(f"p_class == '{p_class}'").copy(deep = True)
            spec_count = 0
            specs = class_df['spec'].unique()
            if len(specs) == 2:
                offsets = [1,3]
            elif len(specs) == 1:
                offsets = [2]
            else:
                offsets = [0,2,4]
            for spec in specs:
                spec_df = class_df.query(f"spec == '{spec}'").copy(deep = True)
                bars.append(go.Bar(
                    x = spec_df.p_class,
                    y = spec_df.counts,
                    name = '',
                    # y = spec_df.counts,
                    width = .15,
                    text = spec_df.spec,
                    hovertemplate = '%{text} %{x} <br> %{y:.2f}',
                    offsetgroup = spec_count,
                    showlegend = False,
                    marker = {'color': colors[p_class]}))
                # bars[-1].hoverlabel = spec
                spec_count += 1
        comp_fig = go.FigureWidget(data=bars)
        comp_fig['layout']['xaxis']['tickangle'] = -30
        comp_fig['layout']['xaxis']['title'] = 'Player Class'
        comp_fig['layout']['yaxis']['title'] = f'Group comp on last pull<br>for.'
        comp_fig.update_traces(textposition='outside')
        comp_fig.update_layout(
            template = 'plotly_dark',
            plot_bgcolor = '#222222',
            paper_bgcolor = '#222222',
            # height=np.ceil(10/2)*200,
            height=400,
            # width = 1000,
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
            title_text=f'{guild_name} composition<br>for {specific_boss}', 
            title_x=0.5
        )
        comp_fig
        return comp_fig


    #%% Make App
    dash_app.layout = html.Div(children=[
        html.H1('Castle Nathria Pull Data', style={'color': 'white', 'backgroundColor':'#222222'}),
        html.Div([
            html.P("Choose guild: ",style={'color': 'white'}),
            dcc.Dropdown(id = 'guild_name',
                        options = [{'label': name, 'value': name} for k, name in enumerate(sorted(guilds))],
                        value = 'Dinosaur Cowboys',
                        style = {'color': 'black',
                                'width': '300px'})
        ]),
        html.Div([
            html.P('Choose Boss', style={'color': 'white'}),        
            dcc.Dropdown(id = 'specific_boss',
                        options = [{'label': name, 'value': name} for k, name in enumerate(boss_names)],
                        value = boss_names[0],
                        style = {'color': 'black',
                                'width': '300px'})
        ]),
        html.Br(style={'backgroundColor':'#222222'}),
        dcc.Graph(
            id='single_guild_graph', style={'backgroundColor':'#222222'}
        ),
        html.Br(),  
        dcc.Graph(
            id='single_guild_comp', style={'backgroundColor':'black'}
        ), 
    html.Br(),   
    html.Br(),   
    html.Br(),
        
    ], style={'backgroundColor':'#222222'})

    return dash_app.server
