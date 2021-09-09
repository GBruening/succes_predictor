from flask import Flask, render_template, send_file

import os
import sys

if sys.platform.lower() == "win32": 
    os.system('color')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/About')
def about():
    return render_template('about.html')

@app.route('/testing')
def plotting():
    return render_template('plot_testing.html')

if __name__ == '__main__':
    app.run(debug = True)

