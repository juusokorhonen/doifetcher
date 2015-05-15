# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

from flask import Flask, url_for, render_template, abort, flash, redirect, session, request, g, current_app
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from flask_wtf.csrf import CsrfProtect
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from jinja2 import TemplateNotFound
from werkzeug import MultiDict
from server.forms import AddArticleForm
from datetime import datetime
import os
import json
import pprint
from server.login import login, lm
from server.export import export
from database.model import db
from server.admin import admin_section
from server.errorhandler import register_errorhandlers 

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
    app.register_blueprint(login)
    lm.init_app(app)
    lm.login_view = 'login.login_page'
    @app.before_request
    def before_request():
        g.user = current_user

    # Import Blueprints
    from server.simple import simple # Use Blueprints
    app.register_blueprint(simple) # register Frontend blueprint

    app.register_blueprint(export)
    
    # Import database model
    db.init_app(app)

    # Admin interface
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
    app.jinja_env.globals['url_for_other_page'] = _jinja2_url_for_other_page
    app.jinja_env.globals['url_for_this_page'] = _jinja2_url_for_this_page

    # Add errorhandler
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
            return sorted(article_list, key=lambda x: x.authors[0].last)
        except:
            return article_list
    else:
        return u''

def equal_args(arg1, arg2):
    if (arg1 == arg2):
        return True
    try:
        if (int(arg1) == int(arg2)):
            return True
    except ValueError:
        pass

    try:
        if (str(arg1) == str(arg2)):
            return True
    except ValueError:
        pass

    try:
        if (unicode(arg1) == unicode(arg2)):
            return True
    except ValueError:
        pass
    
    return False

def convert_type(arg):
    if isinstance(arg, dict):
        newdict = {}
        for key, values in arg.items():
            if isinstance(values, list):
                newdict[key] = [convert_type(value) for value in values]
            else:
                newdict[key] = convert_type(values)
        return newdict

    elif not isinstance(arg, (basestring, unicode)) and isinstance(arg, list):
        return [convert_type(i) for i in arg]

    try:
        return int(arg)
    except:
        pass
    try:
        return str(arg)
    except:
        pass
    try:
        return unicode(arg)
    except:
        pass
    return arg

def _jinja2_url_for_other_page(page, remove=None, **kwargs):
    args = MultiDict()
    if request.view_args is not None and request.view_args != [] and request.view_args != {}:
        args.update(convert_type(request.view_args.copy()))
    if request.args is not None and request.args != [] and request.args != {}:
        args.update(convert_type(request.args.to_dict(flat=False)))

    # Process removes
    if remove is not None:
        if isinstance(remove, (basestring, int)):
            args.poplist(remove)
        elif isinstance(remove, list):
            for item in remove:
                if isinstance(item, (basestring, int)):
                    args.poplist(item)
                elif isinstance(item, tuple):
                    key, value = item
                    arg_values = args.poplist(key)
                    if arg_values is not None and arg_values != []:
                        new_values = [i for i in arg_values if not equal_args(i, value)]
                        args.setlist(key, new_values)
                else:
                    raise ValueError
        elif isinstance(remove, dict):
            for key, value in remove.items():
                if isinstance(value, (basestring, int)):
                    arg_values = args.poplist(key)
                    new_values = [i for i in arg_values if not equal_args(i, value)]
                    args.setlist(key, new_values)
                elif isinstance(value, (list, tuple)):
                    arg_values = args.poplist(key)
                    if arg_values is not None and arg_values != []:
                        new_values = [i for i in arg_values if not equal_args(i, value)]
                        args.setlist(key, new_values)
                else:
                    if current_app.debug:
                        print("Could not parse value : {}".format(value))
                    raise ValueError
        else:
            raise ValueError
   
    if kwargs is not None:
        args.update(convert_type(kwargs.copy()))

    # Remove duplicates
    for key in args.keys():
        items = args.poplist(key)
        items = [convert_type(item) for item in items]
        items = list(set(items))
        args.setlist(key, items)

    return url_for(page, **args)

def _jinja2_url_for_this_page(**kwargs):
    return _jinja2_url_for_other_page(request.endpoint, **kwargs)



