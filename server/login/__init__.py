# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort, redirect, session, g, current_app
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from jinja2 import TemplateNotFound
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from server.forms import *
from database.model import db, User, OAuthUser
from .oauth import *

login = Blueprint(u'login', __name__, template_folder='templates', static_folder='static', static_url_path='/static/login')

# Initialize login manager and openid
lm = LoginManager()

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@login.route('/authorize/<provider>')
def oauth_authorize(provider):
    # TODO: this function is likely to fail if an incorrect provider is supplied
    if not current_user.is_anonymous():
        flash('Already logged in!')
        return redirect(url_for('welcome_page'))
    try:
        oauth = OAuthSignIn.get_provider(provider)
    except Exception as e:
        # We got here, because probably an incorrect oauth provider was supplied
        if current_app.debug:
            print("Getting OAuth provider raised an exception: {}".format(str(e)))
        return abort(404)
    return oauth.authorize()

def check_authorization(authdata):
    return (
            authdata.get('provider') is not None and
            authdata.get('provider') != '' and
            authdata.get('authenticated') and 
            authdata.get('verified') and 
            authdata.get('email') is not None and
            authdata.get('email') != ''
            )

@login.route('/callback/<provider>')
def oauth_callback(provider):
    if current_app.debug:
        print("OAuth Callback called with provider : {}".format(provider))

    if not current_user.is_anonymous():
        flash('Already logged in!')
        return redirect(url_for('welcome_page'))

    oauth = OAuthSignIn.get_provider(provider)
    oauth_data = oauth.callback()

    if not check_authorization(oauth_data):
        if current_app.debug:
            print("OAuth data:")
            for k,v in oauth_data.items():
                print("{} : {}".format(k,v))
        flash('Authentication failed!', category='warning')
        return redirect(url_for('welcome_page'))
   
    provider = oauth_data.get('provider')
    oauth_id = oauth_data.get('id')
    nickname = oauth_data.get('nickname')
    email = oauth_data.get('email')
    name = oauth_data.get('name')

    # TODO: The following fails if there are more than one oauth_id (should not happen, since unique field)
    try:
        oauthuser = OAuthUser.query.filter_by(provider=provider).filter_by(oauth_id=oauth_id).scalar()
    except MultipleResultsFound as e:
        if current_app.debug:
            print("Error. Multiple results were found from unique field: {}".format(str(e)))
        return abort(500)

    if not oauthuser:
        # If oauthuser was not found, we check whether we can match email and nickname to an existing use (potential security hazard!)
        try:
            user = User.query.filter_by(email=email).scalar()
        except MultipleResultsFound as e:
            if current_app.debug:
                print("Error. Multiple results were found from unique field: {}".format(str(e)))
            return abort(500)

        if not user:
            numusers = User.query.count()
            user = User(email=email, nickname=nickname, name=name)
            if numusers == 0:
                # First user is admin
                user.admin = True
            db.session.add(user)

        oauthuser = OAuthUser(provider=provider, oauth_id=oauth_id, user=user)
        db.session.add(oauthuser)
        db.session.commit()

    else:
        user = oauthuser.user

    login_user(user, remember=True)

    flash('Login successful.')
    return redirect(url_for('welcome_page'))

@login.route('/login', methods=['GET'])
def login_page():
    if g.user is not None and g.user.is_authenticated():
        flash('User already logged in')
        return redirect(url_for('welcome_page'))

    return render_template('login.html',
            title='Sign in',
            providers=current_app.config['OAUTH_CREDENTIALS'])

@login.route('/logout')
def logout_page():
    logout_user()
    flash("You have been signed out.")
    return redirect(url_for('welcome_page'))

@login.route('/user/<id_or_nickname>')
@login_required
def profile_page(id_or_nickname):
    user = None
    # First we check whether we are accessing ourselves
    try:
        user_id = int(id_or_nickname)
        if (current_user.id == user_id):
            user = current_user
    except Exception as e:
        if (current_user.nickname == id_or_nickname):
            user = current_user

    # If the search did not match ourselves, then query the database
    if not user:
        try:
            user = User.query.get(int(id_or_nickname))
        except Exception as e:
            if current_app.debug:
                print("Did not find user with id {} : {}".format(id_or_nickname, str(e)))
            # Probably could not map id_or_nickname to integer - that's ok
            pass

        if not user:
            # Could not find id, so let's try nickname
            try:
                user = User.query.filter_by(nickname=id_or_nickname).one()
            except NoResultFound as e:
                if current_app.debug:
                    print("Found no results for nickname {} : {}".format(id_or_nickname, str(e)))
                return abort(404)
            except MultipleResultsFound as e:
                if current_app.debug:
                    print("Found multiple user for nickname {} : {}".format(id_or_nickname, str(e)))
                return abort(404)
    
    if (current_user.id != user.id) and not current_user.is_admin():
        # We are trying to look for another persons account
        if current_app.debug:
            print("Trying to access user information with insufficient permissions.")
        return abort(404) # We send a 404 because otherwise we would reveal that the user exists

    try:
        return render_template('user.html', user=user)
    except TemplateNotFound:
        abort(500)


