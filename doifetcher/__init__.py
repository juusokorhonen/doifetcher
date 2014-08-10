# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask 
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig

def create_app(configfile=None):
	configfile="./config.py"
	app = Flask(__name__)
	AppConfig(app, configfile) # Use of flask-appconfig is highly recommended
	Bootstrap(app) # Use flask-bootstrap
	from doifetcher.frontend import frontend # Use Blueprints
	app.register_blueprint(frontend) # register simple_gui blueprint
	return app
