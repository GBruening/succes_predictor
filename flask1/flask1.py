from flask import Flask, render_template, send_file
import dash
import dash_core_components as dcc
import dash_html_components as html

import os
import sys

if sys.platform.lower() == "win32": 
    os.system('color')

flask_server = Flask(__name__, instance_relative_config=False)
from DashApps.avg_plots_dash2 import init_dashboard as init_agg_dash
from DashApps.single_guild_plotting2 import init_dashboard as init_single_dash

dash_app_agg = init_agg_dash(flask_server)
dash_app_single = init_single_dash(flask_server)

@flask_server.route("/")
def home():
    """Landing page."""
    return render_template(
        "home.html",
        title="TDI Capstone: Better data visualizations and analytics for online video games.",
        description="Embed Plotly Dash into your Flask applications.",
        template="home-template",
        body="This is a homepage served with Flask.",
    )

@flask_server.route('/About/')
def about():
    return render_template('about.html')

@flask_server.route('/SingleGuild/')
def SingleGuild():
    return render_template('SingleGuild.html')

@flask_server.route('/TierStats/')
def TierStats():
    return render_template('TierStats.html')

if __name__ == '__main__':
    # flask_server.run(debug = False)
    flask_server.run(debug = True)

