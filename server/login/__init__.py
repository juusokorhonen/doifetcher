# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort, redirect, session, g, current_app
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
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@login.route('/callback/<provider>')
def oauth_callback(provider):
    if current_app.debug:
        print("OAuth Callback called with provider : {}".format(provider))

    if not current_user.is_anonymous():
        flash('Already logged in!')
        return redirect(url_for('welcome_page'))

    oauth = OAuthSignIn.get_provider(provider)
    oauth_data = oauth.callback()

    if oauth_data.get('id') is None:
        flash('Authentication failed!', category='warning')
        return redirect(url_for('welcome_page'))
    
    nickname = oauth_data.get('nickname')
    email = oauth_data.get('email')
    if nickname is None or nickname == '':
        if email is None or email == '':
            # We have neither email nor nickname: ABORT!
            return error(500)
        nickname = email.split('@')[0]

    # TODO: The following fails if there are more than one oauth_id (should not happen, since unique field)
    oauthuser = OAuthUser.query.filter_by(provider=oauth_data.get('provider')).filter_by(oauth_id=oauth_data.get('id')).first()
    if not oauthuser:
        # If oauthuser was not found, we check whether we can match email and nickname to an existing use (potential security hazard!)
        user = User.query.filter_by(nickname=nickname).filter_by(email=email).first()
        if not user:
            user = User(nickname=nickname, email=email)
            db.session.add(user)

        oauthuser = OAuthUser(provider=oauth_data.get('provider'), oauth_id=oauth_data.get('id'), user=user)
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

@login.route('/user/<nickname>')
@login_required
def profile_page(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if (g.user.id != user.id) and not g.user.is_admin():
        # We are trying to look for another persons account
        abort(404) # We send a 404 because otherwise we would reveal that the user exists
    if user == None:
        flash("User %s not found." % nickname)
        return redirect(url_for('welcome_page'))
    try:
        return render_template('user.html', user=user)
    except TemplateNotFound:
        abort(500)


