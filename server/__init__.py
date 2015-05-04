# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

from flask import Flask, url_for, render_template, abort, flash, redirect, session, request, g
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from flask_wtf.csrf import CsrfProtect
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from jinja2 import TemplateNotFound
from server.forms import AddArticleForm
from datetime import datetime
import os
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
    
    # Enable CSRF protection (not really sure if this is needed or not - it's needed for views without forms)
    #CsrfProtect(app)
    
    # Enable login and openid
    from server.login import login, lm
    app.register_blueprint(login)
    lm.init_app(app)
    lm.login_view = 'login.login_page'
    @app.before_request
    def before_request():
        g.user = current_user

    # Import Blueprints
    from server.simple import simple # Use Blueprints
    app.register_blueprint(simple) # register Frontend blueprint

    from server.export import export
    app.register_blueprint(export)
    
    # Import database model
    from database.model import db
    db.init_app(app)

    # Admin interface
    from server.admin import admin_section
    admin_section.init_app(app)
    admin_section.init_db(db)
    admin_section.name = u"{} :: {}".format(app.config.get('SITE_TITLE', 'DOI Fetcher'), u"Admin Interface")
    
    
    # Development-specific functions 
    if (app.debug):
        pass
    # Testing-specifig functions
    if (app.config.get('TESTING')):
        pass
    # Production-specific functions
    if (app.config.get('PRODUCTION')):
        pass

    # Add custom filter to jinja
    app.jinja_env.filters['prettyjson'] = _jinja2_filter_prettyjson
    app.jinja_env.filters['sn'] = _jinja2_filter_supress_none
    app.jinja_env.filters['sort_by_first_author'] = _jinja2_sort_by_first_author

    # Add errorhandler
    from server.errorhandler import register_errorhandlers 
    register_errorhandlers(app)
    
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

def _jinja2_sort_by_first_author(article_list):
    if article_list is not None:
        try:
            #for article in article_list:
            #    print(article.authors[0].last)
            return sorted(article_list, key=lambda x: x.authors[0].last)
        except:
            return article_list
    else:
        return u''
