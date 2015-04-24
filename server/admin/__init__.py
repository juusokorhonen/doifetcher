# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort, g
from jinja2 import TemplateNotFound
from flask.ext.superadmin import Admin, BaseView, expose, model, AdminIndexView
from flask.ext.superadmin.contrib.sqlamodel import ModelView
from flask.ext.login import login_required, current_user
#from flask.ext.superadmin.contrib.sqla import ModelView
from database.model import Article, Author, Journal, User, OAuthUser


class _AdminView(AdminIndexView):
    @expose('/')
    def index(self):
        if current_app.debug:
            print("_AdminView index hit.")
        return self.render('admin/index.html')

    def is_accessible(self):
        if current_app.debug:
            print("is_accessible() at _AdminView hit with user {}".format(current_user))
        return current_user.is_authenticated()

class _DbModel(model.ModelAdmin):
    list_template = 'admin/list.html'
    edit_template = 'admin/edit.html'
    def is_accessible(self):
        if current_app.debug:
            print("is_accessible() at _DbModel hit with user {}".format(current_user))
        return current_user.is_authenticated()

class _AdminDbModel(_DbModel):
    def is_accessible(self):
        if current_app.debug:
            print("is_accessible() at _AdminDbModel hit with use {}".format(current_user))
        return current_user.is_authenticated() and current_user.is_admin()

admin_section = Admin(index_view=_AdminView())

import types
# Initialize database connection
def init_db(self, db):
    self.register(Article, _DbModel, session=db.session)
    self.register(Author, _DbModel, session=db.session)
    self.register(Journal, _DbModel, session=db.session)
    self.register(User, _AdminDbModel, session=db.session)
    self.register(OAuthUser, _AdminDbModel, session=db.session)

# Bind the method to the object
admin_section.init_db = types.MethodType(init_db, admin_section)

