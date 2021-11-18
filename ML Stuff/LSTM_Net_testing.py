#%%
# %%

# LSTM and CNN for sequence classification in the IMDB dataset
import numpy as np
import pandas as pd
import ast
from joblib import dump, load
import joblib
import pickle

from itertools import product
import pickle
from os import path

import os
from sqlalchemy import create_engine
import psycopg2

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

#%% Functions


# %% Setup
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


# %% Get the data sets
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
boss = boss_names[-1]

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
        if isinstance(X, list):
            return X
        else:
            return [ast.literal_eval(item) for item in list(X['pulls'])]

def build_model(**kwargs):
    pull_pipe = Pipeline([
        ('encoder', pull_encoder()),
        ('pull_classifier', RandomForestClassifier(bootstrap = True, n_jobs = 5))
    ])
    params_pulls = {'pull_classifier__max_depth': kwargs['max_depth'],
                    'pull_classifier__min_samples_leaf': kwargs['min_s_leaf'],
                    'pull_classifier__n_estimators': kwargs['n_est']}

    pull_pipe.set_params(**params_pulls)
    full_pipe = pull_pipe

    return full_pipe

#%%
for boss in boss_names:
    print(f'Fitting boss: {boss}')
    boss_csv = str(boss.replace(' ','_'))
    data = pd.read_csv(f'pull_list_{boss_csv}.csv')

    pull_list = [ast.literal_eval(item) for item in list(data['pulls'])]
    ilvl_list = list(data['ilvl'])
    kill_list = list(data['kills'])

    kwargs = {'max_depth': [5,10,20],
            'min_s_leaf': [5, 20, 50],
            'n_est': [50, 100, 500]}#,
            # 'alpha': [10]}

    # scores = []
    max_depth  = []
    min_s_leaf = []
    n_est      = []
    scores = []
    n_cv = 5
    for k, combin in enumerate(product(*kwargs.values())):
        for cv in range(0,n_cv):
            if (combin[0] in max_depth and 
                combin[1] in min_s_leaf and 
                combin[2] in n_est):
                print(f'Skipping {k+1}', end = '\r')
                continue
                
            kwarg = {'max_depth':  combin[0],
                    'min_s_leaf': combin[1],
                    'n_est':      combin[2]}

            full_pipe = build_model(**kwarg)

            X_train, X_test, y_train, y_test = train_test_split(data, data['kills'], test_size = 0.2)
            full_pipe.fit(X_train, y_train)
            
            print(f'Iter: {k+1}, Score: 1, Fitted {kwarg}', end = '\r')

    # df = pd.DataFrame(scores, columns = ['max_depth', 'min_s_leaf', 'min_split','n_est','alpha', 'last_alpha', 'score'])
    # df = df.groupby(['max_depth', 'min_s_leaf', 'min_split','n_est','alpha', 'last_alpha']).agg({'score': ['mean']}).reset_index()
    df = pd.DataFrame(scores, columns = ['max_depth', 'min_s_leaf','n_est', 'score'])
    df = df.groupby(['max_depth', 'min_s_leaf', 'n_est']).agg({'score': ['mean']}).reset_index()

    maxdf = df.loc[df['score']['mean'].argmax()]

    kwarg = {'max_depth': int(maxdf['max_depth']),
            'min_s_leaf': float(maxdf['min_s_leaf']),
            # 'min_split': int(maxdf['min_split']),
            'n_est': int(maxdf['n_est']),
            # 'alpha': float(maxdf['alpha']),
            'last_alpha': 1}

    full_pipe = build_model(**kwarg)
    full_pipe.fit(data, data['kills'])

    boss_str = str(boss.replace(' ','_'))
    filename = f'{boss_str}_mod.pickle'

    joblib.dump(full_pipe, filename)

asdfasdf