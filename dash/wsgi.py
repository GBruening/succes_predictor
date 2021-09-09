"""Application entry point."""
from plotlyflask_tutorial import init_app
from flask import Flask, render_template, send_file
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = init_app()

if __name__ == '__main__':
    app.run(debug = True)
