"""Application entry point."""
from plotlyflask_tutorial import init_app
from flask import Flask, render_template, send_file
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = init_app()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/About')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug = True)
