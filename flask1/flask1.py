from flask import Flask, render_template, send_file

import os
import sys

if sys.platform.lower() == "win32": 
    os.system('color')

flask_app = Flask(__name__)

single_guild_dash = dash.Dash(__name__, server=app_flask, url_base_pathname='/pathname')

@flask_app.route('/')
def index():
    return render_template('home.html')

@flask_app.route('/About')
def about():
    return render_template('about.html')

@flask_app.route('/testing')
def plotting():
    return render_template('plot_testing.html')

if __name__ == '__main__':
    flask_app.run(debug = True)

