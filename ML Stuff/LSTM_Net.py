#%%
# %%

# LSTM and CNN for sequence classification in the IMDB dataset
import numpy as np
import pandas as pd
import ast
from joblib import dump, load
import joblib
import pickle

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

# for boss in reversed(boss_names[5:-1]):
print(f'Fitting boss: {boss}')
boss_csv = str(boss.replace(' ','_'))
data = pd.read_csv(f'pull_list_{boss_csv}.csv')

pull_list = [ast.literal_eval(item) for item in list(data['pulls'])]
# pull_list = [item.strip('][').split(', ') for item in list(data['pulls'])]
# data['pulls'] = list(pull_list)
ilvl_list = list(data['ilvl'])
kill_list = list(data['kills'])

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
        ('pull_classifier', RandomForestClassifier(bootstrap = True, n_jobs = 5))
    ])
    params_pulls = {'pull_classifier__max_depth': kwargs['max_depth'],
                    'pull_classifier__min_samples_leaf': kwargs['min_s_leaf'],
                    'pull_classifier__min_samples_split': kwargs['min_split'],
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

# kwargs = {'max_depth': 5,
#           'min_s_leaf': 10,
#           'min_split': 5,
#           'n_est': 50,
#           'alpha': 1,
#           'last_alpha': 10}

# full_pipe = build_model(**kwargs)

# X_train, X_test, y_train, y_test = train_test_split(data, data['kills'], test_size = 0.2)

# full_pipe.fit(X_train, y_train)


from itertools import product
import pickle
from os import path
# pickle.dump(full_mod, open('full_mod.pickle', 'wb'))

kwargs = {'max_depth': [5,10,20],
          'min_s_leaf': [10,20],
          'min_split': [5,15],
          'n_est': [100],
          'alpha': [.1,10],
          'last_alpha': [.1,10]}

scores = []
if path.exists('score_keeper.pickle'):
    scores = pickle.load(open("score_keeper.pickle",'rb'))
    max_depth  = [score[0] for score in scores]
    min_s_leaf = [score[1] for score in scores]
    min_split  = [score[2] for score in scores]
    n_est      = [score[3] for score in scores]
    alpha      = [score[4] for score in scores]
    last_alpha = [score[5] for score in scores]
else:
    max_depth  = []
    min_s_leaf = []
    min_split  = []
    n_est      = []
    alpha      = []
    last_alpha = []
    scores = []
n_cv = 5
for k, combin in enumerate(product(*kwargs.values())):
    for cv in range(0,n_cv):
        if (combin[0] in max_depth and 
            combin[1] in min_s_leaf and 
            combin[2] in min_split and 
            combin[3] in n_est and 
            combin[4] in alpha and 
            combin[5] in last_alpha):
            print(f'Skipping {k+1}', end = '\r')
            continue
            
        kwarg = {'max_depth':  combin[0],
                 'min_s_leaf': combin[1],
                 'min_split':  combin[2],
                 'n_est':      combin[3],
                 'alpha':      combin[4],
                 'last_alpha': combin[5]}

        full_pipe = build_model(**kwarg)

        X_train, X_test, y_train, y_test = train_test_split(data, data['kills'], test_size = 0.2)
        full_pipe.fit(X_train, y_train)
        
        score = full_pipe.score(X_test, y_test)
        scores.append((combin[0], combin[1], combin[2], combin[3], combin[4], score))
        pickle.dump(scores, open('score_keeper.pickle', 'wb'))
        print(f'Iter: {k+1}, Score: {score}, Fitted {kwarg}', end = '\r')


if path.exists('score_keeper.pickle'):
    scores = pickle.load(open("score_keeper.pickle",'rb'))
df = pd.DataFrame(scores, columns = ['max_depth', 'min_s_leaf', 'min_split','n_est','alpha','last_alpha', 'score'])
df = df.groupby(['max_depth', 'min_s_leaf', 'min_split','n_est','alpha','last_alpha', ]).agg({'score': ['mean']}).reset_index()

maxdf = df.loc[df['score']['mean'].argmax()]

kwarg = {'max_depth': int(maxdf['max_depth']),
         'min_s_leaf': float(maxdf['min_s_leaf']),
         'min_split': int(maxdf['min_split']),
         'n_est': int(maxdf['n_est']),
         'alpha': float(maxdf['alpha']),
         'last_alpha': float(maxdf['last_alpha'])}

full_pipe = build_model(**kwarg)
full_pipe.fit(data, data['kills'])

boss_str = str(boss.replace(' ','_'))
filename = f'{boss_str}_mod.pickle'
joblib.dump(full_pipe, filename)

#%%
# class pullmodel(BaseEstimator, RegressorMixin):
#     def __init__(self, depth = 3, minleaf = 20, minsplit = 10):
#         self.max_depth = depth
#         self.min_samples_leaf = minleaf
#         self.min_samples_split = minsplit
#         self = self
        
#     def predict(self, X):
        
#         # lin_predict = self.lin_model.predict(X)
#         # nonlin_predict = self.nonlin_model.predict(X)
#         # output = lin_predict + nonlin_predict
#         output = self.tree_model.predict(X)
#         return output
        
#     def fit(self, X, y, alpha1, depth, minleaf, minsplit):

#         # ridge_fit = Ridge(alpha = alpha1)
#         # self.lin_model = ridge_fit.fit(X, y)
        
#         # residuals = y - self.lin_model.predict(X)
#         d_tree = RandomForestClassifier(bootstrap = True,
#             max_depth = depth,
#             min_samples_leaf = minleaf,
#             min_samples_split = minsplit,
#             n_estimators = 200)
#         self.tree_model = d_tree.fit(X, y)
#         return self


# encode class values as integers
# LSTM with dropout for sequence classification in the IMDB dataset
import numpy
numpy.random.seed(7)

from sklearn import datasets, tree, utils
# import graphviz 
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split 
from sklearn.datasets import make_classification

X_train, X_test, Y_train, Y_test = train_test_split(pull_list, kill_list, test_size = .1) 

# tree_clf = tree.DecisionTreeClassifier(max_depth=3).fit(X_train, Y_train)
# tree_clf.score(X_test, Y_test)

clf = RandomForestClassifier(n_estimators = 200,
                                n_jobs = 5)

param_grid = {
    'bootstrap': [True],
    'max_depth': [8,12],
    'min_samples_leaf': [5,10],
    'min_samples_split': [10,25],
    'n_estimators': [100, 200]
}

grid_search = GridSearchCV(clf, param_grid = param_grid,
                        cv = 5, n_jobs = 8, verbose = 5)
grid_search.fit(pull_list, kill_list)
# grid_search.score(X_test, Y_test)
# grid_search.fit(pull_list, kill_list)

boss_str = str(boss.replace(' ','_'))
# pickle.dump(grid_search, open(boss_str, 'w'))

filename = f'{boss_str}_mod.pickle'
joblib.dump(grid_search, filename)

loaded_model = joblib.load(filename)

asdfs
#%%

from sklearn import model_selection, ensemble

# cv = model_selection.ShuffleSplit(n_splits=5, test_size=0.2, random_state=42)
# rf = model_selection.cross_val_score(clf, X_train, Y_train, cv=cv, 
#                                 scoring='neg_mean_squared_error', 
#                                 verbose = 2, 
#                                 n_jobs = 5)
# clf.estimators_[0].feature_importances_


# %%



from keras.datasets import imdb
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence
# fix random seed for reproducibility
# create the model
model = Sequential()
model.add(LSTM(100, dropout=0.2, recurrent_dropout=0.2))
model.add(Dense(1, activation='sigmoid'))
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X_train, Y_train, epochs=1, batch_size=64)
print(model.summary())
# Final evaluation of the model
scores = model.evaluate(X_test, Y_test, verbose=0)
print("Accuracy: %.2f%%" % (scores[1]*100))