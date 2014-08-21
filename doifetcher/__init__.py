# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, url_for
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig

def create_app(config=None, configfile=None):
    """
    Creates a Flask app using the provided configuration.

    Keyword arguments:
    :param config:  Config object or None (default: None)
    :param configfile: - Name and path to configfile (default: None)
    :returns: Flask application
    """
    app = Flask(__name__)
    # Configure app
    AppConfig(app, default_settings=config, configfile=configfile) # Use of flask-appconfig is highly recommended
    Bootstrap(app) # Use flask-bootstrap
    # Import Blueprints
    from doifetcher.frontend import frontend # Use Blueprints
    app.register_blueprint(frontend) # register Frontend blueprint
    # Import database model
    from doifetcher.model import db
    db.init_app(app)
    # Development purposes
    from doifetcher.model import populate_example_data
    populate_example_data(app,db)
    return app
