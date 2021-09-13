"""Application entry point."""
from plotlyflask_tutorial import init_app
import os
from flask import Flask
from flask_assets import Environment
from flask import current_app as app
from flask_assets import Bundle

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def compile_static_assets(assets):
    """
    Compile stylesheets if in development mode.

    :param assets: Flask-Assets Environment
    :type assets: Environment
    """
    assets.auto_build = True
    assets.debug = False
    less_bundle = Bundle(
        "less/*.less",
        filters="less,cssmin",
        output="dist/css/styles.css",
        extra={"rel": "stylesheet/less"},
    )
    assets.register("less_all", less_bundle)
    if app.config["FLASK_ENV"] == "development":
        less_bundle.build()
    return assets

def init_app():
    """Construct core Flask application with embedded Dash app."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config.Config")
    assets = Environment()
    assets.init_app(app)

    with app.app_context():
        # Import parts of our core Flask app
        from . import routes
        from .assets import compile_static_assets

        # Import Dash application
        from .plotlydash.dashboard import init_dashboard

        app = init_dashboard(app)

        # Compile static assets
        compile_static_assets(assets)

        return app

app = init_app()

"""Routes for parent Flask app."""
from flask import current_app as app
from flask import render_template

@app.route("/")
def home():
    """Landing page."""
    return render_template(
        "index.jinja2",
        title="Plotly Dash Flask Tutorial",
        description="Embed Plotly Dash into your Flask applications.",
        template="home-template",
        body="This is a homepage served with Flask.",
    )

if __name__ == '__main__':
    app.run(debug = True)