#%%
# %%

# LSTM and CNN for sequence classification in the IMDB dataset
import numpy as np
import pandas as pd
import ast

from keras.datasets import imdb
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence

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

temp = pd.read_csv('pull_list_Shriekwing.csv')

pull_list = [ast.literal_eval(item) for item in list(temp['pulls'])]
kill_list = list(temp['kills'])

# %%
# encode class values as integers
# LSTM with dropout for sequence classification in the IMDB dataset
import numpy
numpy.random.seed(7)

from sklearn import datasets, tree, utils
# import graphviz 
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split 
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification

X_train, X_test, Y_train, Y_test = train_test_split(pull_list, kill_list, test_size = .1) 

# tree_clf = tree.DecisionTreeClassifier(max_depth=3).fit(X_train, Y_train)
# tree_clf.score(X_test, Y_test)

clf = RandomForestClassifier(n_estimators = 200,
                             n_jobs = 5)

# clf = RandomForestClassifier(max_depth=4,
#                              random_state=0,
#                              oob_score=True,
#                              n_jobs = 5)
# clf.fit(X_train, Y_train)
# clf.predict_proba([[100, 100, 100, 100, 100, 100, 100, 100, 100, 100]])
# clf.score(X_test, Y_test)

param_grid = {
    'bootstrap': [True],
    'max_depth': [1,5,10,40],
    'min_samples_leaf': [3, 4, 5],
    'min_samples_split': [8, 10, 12],
    'n_estimators': [100, 200, 300, 1000]
}

grid_search = GridSearchCV(clf, param_grid = param_grid,
                           cv = 5, n_jobs = 3, verbose = 5)
grid_search.fit(pull_list, kill_list)



from sklearn import model_selection, ensemble

cv = model_selection.ShuffleSplit(n_splits=5, test_size=0.2, random_state=42)
model_selection.cross_val_score(clf, X_train, Y_train, cv=cv, 
                                scoring='neg_mean_squared_error', 
                                verbose = 2, 
                                n_jobs = 5)
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