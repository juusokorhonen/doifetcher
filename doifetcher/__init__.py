# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask 
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig

def create_app(configfile=None):
    configfile="./config.py"
    app = Flask(__name__)
    # Configure app
    AppConfig(app, configfile) # Use of flask-appconfig is highly recommended
    Bootstrap(app) # Use flask-bootstrap
    # Import Blueprints
    from doifetcher.frontend import frontend # Use Blueprints
    app.register_blueprint(frontend) # register simple_gui blueprint
    # Import database model
    from doifetcher.model import db
    db.init_app(app)
    # Development purposes
    from doifetcher.model import populate_example_data
    populate_example_data(app,db)
    return app
