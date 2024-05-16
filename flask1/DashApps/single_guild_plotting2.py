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
from dotenv import load_dotenv, dotenv_values
from requests_oauthlib import OAuth2, OAuth2Session
import requests
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

def get_one_guild_pulls(specific_boss, guild_name):
    specific_boss = specific_boss.replace("'", "''")
    try:
        curs2.execute(f"Select *, log_start+start_time as fight_start_time\
            from nathria_prog_v2 where name = '{specific_boss}' and guild_name = '{guild_name}';")

        pull_df = pd.DataFrame(curs2.fetchall())
        pull_df.columns = [desc[0] for desc in curs2.description]

        pull_df = rm_repeat_boss(pull_df)
    except:
        pull_df = pd.read_csv(dname+'/../../Pulling data/only_first_kill_players.csv').query(f"guild_name == '{guild_name}' and boss_name == '{specific_boss}'")
        
    return pull_df

def make_fights_query_onefight(fight):
    code = fight['log_code']
    fight_ID = int(fight['id'])
    start_time = fight['start_time']
    end_time = fight['end_time']
    query = """
    {
    reportData{
        report(code: "%s"){
        table(fightIDs: %s, startTime: %s, endTime: %s)
        }
    }
    }
    """ % (code, fight_ID, str(start_time), str(end_time))

    return query

def get_fight_args(log, graphql_endpoint, headers):
    args = {'url': graphql_endpoint,
            'json': {'query': make_fights_query_onefight(log)},
            'headers': headers}
    return args

def parse_fight_table(table, boss_name, unique_id, guild_name):

    comp = table['composition']
    roles = table['playerDetails']
    player_list = []
    for role in roles:
        players = roles[role]
        for player in players:
            try:
                gear_ilvl = [piece['itemLevel'] for piece in player['combatantInfo']['gear']]
                ilvl = np.mean(gear_ilvl)
            except:
                try:
                    ilvl = player['minItemLevel']
                except:
                    ilvl = np.NaN
            
            try:
                server = player['server']
                class_ = player['type']
            except:
                server = np.NaN
                class_ = np.NaN
            try:
                covenant = player['combatantInfo']['covenantID']
            except:
                covenant = np.NaN

            try:
                spec = player['specs'][0]
            except:
                spec = np.NaN

            try:
                stats = player['combatantInfo']['stats']
                primaries = ['Agility','Intellect','Strength']
                for primary in primaries:
                    if primary in stats.keys():
                        break
                primary= stats[primary]['min']
                mastery= stats['Mastery']['min']
                crit= stats['Crit']['min']
                haste= stats['Haste']['min']
                vers= stats['Versatility']['min']
                stamina= stats['Stamina']['min']
            except:
                primary = np.NaN
                mastery = np.NaN
                crit = np.NaN
                haste = np.NaN
                vers = np.NaN
                stamina = np.NaN
        
            player_info= {'unique_id': unique_id,
                        'player_name': player['name'],
                        'guild_name': guild_name,
                        'server': server,
                        'class': class_,
                        'spec': spec,
                        'role': role,
                        'ilvl': ilvl,
                        'covenant': covenant,
                        'primary': primary,
                        'mastery': mastery,
                        'crit': crit,
                        'haste': haste,
                        'vers': vers,
                        'stamina': stamina,
                        'boss_name': boss_name}
            player_list.append(player_info)
    return player_list


from sklearn.base import BaseEstimator, RegressorMixin, TransformerMixin
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
from sklearn.linear_model import RidgeClassifier

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.model_selection import train_test_split 
from sklearn.ensemble import RandomForestClassifier

class ModelTransformer(BaseEstimator, TransformerMixin):    
    def __init__(self, model):
        self.model = model
        # What needs to be done here?
    
    def fit(self, X, y, **kwargs):
        self.model.fit(X, y)
        return self
        # Fit the stored predictor.
        # Question: what should be returned?
    
    def transform(self, X):
        return np.array(self.model.predict(X)).reshape(-1, 1)
        # Use predict on the stored predictor as a "transformation".
        # Be sure to return a 2-D array.

class pull_encoder(BaseEstimator, TransformerMixin):
    def fit(self, X, y = None):
        return self
    
    def transform(self, X):
        return [ast.literal_eval(item) for item in list(X['pulls'])]

def build_model(**kwargs):
    # selector = ColumnTransformer(transformers = [('pulls','passthrough',[0])])
    pull_pipe = Pipeline([
        # ('features', ColumnTransformer(transformers = [('pulls','passthrough',[0])])),
        ('encoder', pull_encoder()),
        ('pull_classifier', RandomForestClassifier(bootstrap = True, n_jobs = 10))
    ])
    params_pulls = {'pull_classifier__max_depth': kwargs['max_depth'],
                    'pull_classifier__min_samples_leaf': kwargs['min_s_leaf'],
                    # 'pull_classifier__min_samples_split': kwargs['min_split'],
                    'pull_classifier__n_estimators': kwargs['n_est']}
    pull_pipe.set_params(**params_pulls)
    pull_trans = ModelTransformer(pull_pipe)
    # pull_trans.fit(data, kill_list)

    ilvl_feat = ColumnTransformer(transformers = [('ilvl','passthrough',[1])])
    ilvl_pipe = Pipeline([
        ('features', ilvl_feat),
        ('ilvl_regressor', RidgeClassifier())
    ])
    params_ilvl = {'ilvl_regressor__alpha': kwargs['alpha']}
    ilvl_pipe.set_params(**params_ilvl)
    ilvl_trans = ModelTransformer(ilvl_pipe)
    # ilvl_trans.fit(data, kill_list)

    union = FeatureUnion([
        ('pulls', pull_trans),
        ('ilvl', ilvl_trans)
    ])

    full_pipe = Pipeline([
        ('union', union),
        ('regression', RidgeClassifier(alpha = kwargs['last_alpha']))
    ])

    return full_pipe


#%% Create Data
import numpy as np
import json
import os
import time
from datetime import datetime

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
print(os.listdir(dname+'\\..\\..\\Pulling Data\\'))
print(dname)
print(dname)
print(dname)
print(dname)
print(dname)
print(os.path.isfile(dname+'\\..\\..\\Pulling Data\\refresh_token.env'))

if os.path.isfile(dname+'\\..\\..\\Pulling Data\\refresh_token.env'):
    env_vars = dotenv_values(dname+'\\..\\..\\Pulling Data\\refresh_token.env')
    refresh_token = env_vars['refresh_token']
    access_token = env_vars['access_token']

    env_vars = dotenv_values(dname+'\\..\\..\\Pulling Data\\config.env')
    client_id = env_vars['id']
    client_secret = env_vars['secret']
    code = env_vars['code']

    graphql_endpoint = "https://www.warcraftlogs.com/api/v2/client"
    headers = {"Authorization": f"Bearer {access_token}"}

    callback_uri = "http://localhost:8080"
    authorize_url = "https://www.warcraftlogs.com/oauth/authorize"
    token_url = "https://www.warcraftlogs.com/oauth/token"

    warcraftlogs = OAuth2Session(client_id = client_id)
else:
    raise 'Get your fresh token dumby'

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
    curs2 = conn.cursor()
except:
    print(f'No database found, using csvs.')


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

    try:
        curs.execute('select distinct guild_name from nathria_prog')
        guilds = [item[0] for item in curs.fetchall()]
    except:
        data = pd.read_csv(dname+'/../../Pulling data/nathria_prog_small.csv')
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
    @dash_app.callback(
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
            filename = dname+f'.\{model_specific_boss}_mod.pickle'
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

    @dash_app.callback(
        Output('single_guild_comp', 'figure'),
        Input('guild_name', 'value'),
        Input('specific_boss', 'value')
    )
    def create_single_guild_comp(guild_name, specific_boss):
        specific_boss = specific_boss.replace("'", "''")

        pulls_for_comp = get_one_guild_pulls(specific_boss, guild_name)
        
        try:
            first_kill = pulls_for_comp.query('kill == 1.0')
            if len(first_kill) > 0:
                first_time = first_kill.loc[first_kill['fight_start_time'].idxmin()]['fight_start_time']
                pulls_for_comp = pulls_for_comp.query(f'fight_start_time < {first_time+10}')
            last_pull = pulls_for_comp.tail(1).to_dict(orient="records")[0]
            last_pull['id'] = int(last_pull['id'])

            result = requests.post(**get_fight_args(last_pull, graphql_endpoint, headers))
            table = result.json()['data']['reportData']['report']['table']['data']

            player_info = parse_fight_table(table, 
                last_pull['name'], 
                last_pull['unique_id'], 
                guild_name)
            player_df = pd.DataFrame.from_dict(player_info)

            player_df['test'] = player_df[player_df.columns[4:7]].apply(
                lambda x: ', '.join(x.dropna().astype(str)),
                axis=1
            )
        except:
            player_df = pulls_for_comp

            player_df['test'] = player_df[player_df.columns[5:8]].apply(
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
            html.P("All pulls or Progression Pulls?", style={'color': 'white'}),        
            dcc.RadioItems(options=[
                {'label': 'All Pulls', 'value': 'all_pulls'},
                {'label': 'Progression Only', 'value': 'prog_only_pulls'}
            ],
            id = 'prog_or_all',
            value = 'all_pulls',
            labelStyle={'color': 'white',
                        'display': 'flex'}
            )
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
