# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, url_for, render_template, abort
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from jinja2 import TemplateNotFound
from doifetcher.forms import AddArticleForm
import json
import pprint

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
    from doifetcher.simple import simple # Use Blueprints
    app.register_blueprint(simple) # register Frontend blueprint
    from doifetcher.browse import browse
    app.register_blueprint(browse)
    from doifetcher.batch import batch
    app.register_blueprint(batch)
    from doifetcher.export import export
    app.register_blueprint(export)
    # Import database model
    from doifetcher.model import db
    db.init_app(app)
    # Development purposes
    from doifetcher.model import populate_example_data
    populate_example_data(app,db)
    # Add custom filter to jinja
    app.jinja_env.filters['prettyjson'] = _jinja2_filter_prettyjson
    app.jinja_env.filters['sn'] = _jinja2_filter_supress_none

    # Add frontpage
    @app.route('/')
    def welcome_page():
        form = AddArticleForm()
        try:
            return render_template('index.html', form=form)
        except TemplateNotFound:
            abort(404)

    return app


def _jinja2_filter_prettyjson(jsondata):
    if jsondata:
        return pprint.pformat(json.loads(jsondata))
    else: 
        return u""

def _jinja2_filter_supress_none(val):
    if val is not None:
        return val
    else:
        return u''
