# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask 
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig

configfile="./config.py"
app = Flask(__name__)
AppConfig(app, configfile) # Use of flask-appconfig is highly recommended
Bootstrap(app) # Use flask-bootstrap
import doifetcher.views # Import views, ie. app.route's
