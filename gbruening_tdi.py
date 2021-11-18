#%%
from flask import Flask, render_template, send_file

import dash
import dash_bootstrap_components as dbc
from dash import Dash
from dash import dcc
from dash import html
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
import os
import sys

from sklearn.base import BaseEstimator, RegressorMixin, TransformerMixin
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
from sklearn.linear_model import RidgeClassifier

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.model_selection import train_test_split 
from sklearn.ensemble import RandomForestClassifier
if sys.platform.lower() == "win32": 
    os.system('color')

#%%
app = Flask(__name__, instance_relative_config=False)
from DashApps.avg_plots_dash2 import init_dashboard as init_agg_dash
from DashApps.single_guild_plotting2 import init_dashboard as init_single_dash

dash_app_agg = init_agg_dash(app)
dash_app_single = init_single_dash(app)

class pull_encoder(BaseEstimator, TransformerMixin):
    def fit(self, X, y = None):
        return self
    
    def transform(self, X):
        if isinstance(X, list):
            return X
        else:
            return [ast.literal_eval(item) for item in list(X['pulls'])]

@app.route("/")
def home():
    """Landing page."""
    return render_template(
        "home.html",
        title="TDI Capstone: Better data visualizations and analytics for online video games.",
        description="Embed Plotly Dash into your Flask applications.",
        template="home-template",
        body="This is a homepage served with Flask.",
    )

@app.route('/About/')
def about():
    return render_template('about.html')

# @app.route('/SingleGuild/')
# def SingleGuild():
#     return render_template('SingleGuild.html')

# @app.route('/TierStats/')
# def TierStats():
#     return render_template('TierStats.html')

if __name__ == '__main__':
    app.run(debug = False)
    # app.run(debug = True)

