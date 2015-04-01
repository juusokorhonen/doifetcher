# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort, redirect, session, g, current_app
from jinja2 import TemplateNotFound
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from flask.ext.openid import OpenID

from server.forms import *
from database.model import db, User

login = Blueprint(u'login', __name__, template_folder='templates', static_folder='static', static_url_path='/static/login')

# Initialize login manager and openid
lm = LoginManager()
oid = OpenID()

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@login.route('/login', methods=['GET','POST'])
@oid.loginhandler
def login_page():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('welcome_page'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'], ask_for_optional=['fullname'])
    return render_template('login.html',
            next=oid.get_next_url(),
            error=oid.fetch_error(),
            title='Sign in',
            form=form,
            providers=current_app.config['OPENID_PROVIDERS'])

@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash("Invalid login. Please try again.")
        return redirect(url_for('login_page'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname=User.make_unique_nickname(nickname), email=resp.email, openid=resp.identity_url, name=resp.fullname)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    flash ("Login successful.")
    return redirect(oid.get_next_url() or url_for('welcome_page'))

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
