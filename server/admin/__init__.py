# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort, g
from jinja2 import TemplateNotFound
from flask.ext.admin import Admin, BaseView, expose, model, AdminIndexView
from flask.ext.login import login_required, current_user
from flask.ext.admin.contrib.sqla import ModelView
from database.model import Article, Author, Journal, Tag, User, OAuthUser


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

class _DbModel(ModelView):
    def is_accessible(self):
        if current_app.debug:
            print("is_accessible() at _DbModel hit with user {}".format(current_user))
        return current_user.is_authenticated()

    def __init__(self, model, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(_DbModel, self).__init__(model, session, **kwargs)

class _AdminDbModel(_DbModel):
    def is_accessible(self):
        if current_app.debug:
            print("is_accessible() at _AdminDbModel hit with use {}".format(current_user))
        return current_user.is_authenticated() and current_user.is_admin()

admin_section = Admin(index_view=_AdminView())

class ArticleView(_DbModel):
    _model = Article
    column_exclude_list = ['json_data', 'doi', 'add_date', 'mod_date', 'inserter', 'inserter_ip']
    column_searchable_list = ('id', 'doi', 'title', 'add_date')
    column_default_sort = ('pub_date', True)
    column_filters = ('pub_date', 'journal')
    
    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(ArticleView, self).__init__(self._model, session, **kwargs)


class AuthorView(_DbModel):
    _model = Author
    column_searchable_list = ('first', 'middle', 'last', 'nickname')
    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(AuthorView, self).__init__(self._model, session, **kwargs)

class JournalView(_DbModel):
    _model = Journal 
    column_searchable_list = ('name', 'abbreviation')
    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(JournalView, self).__init__(self._model, session, **kwargs)

class TagView(_DbModel):
    _model = Tag
    column_searchable_list = ('name',)
    def __init__(self, session, **kwargs):
        super(TagView, self).__init__(self._model, session, **kwargs)

class UserView(_AdminDbModel):
    _model = User
    column_searchable_list = ('email', 'nickname', 'name')
    column_filters = ('admin', )
    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(UserView, self).__init__(self._model, session, **kwargs)

class OAuthUserView(_AdminDbModel):
    _model = OAuthUser
    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(OAuthUserView, self).__init__(self._model, session, **kwargs)

import types
# Initialize database connection
def init_db(self, db):
    self.add_view(ArticleView(db.session))
    self.add_view(AuthorView(db.session))
    self.add_view(JournalView(db.session))
    self.add_view(TagView(db.session))
    self.add_view(UserView(db.session))
    self.add_view(OAuthUserView(db.session))

# Bind the method to the object
admin_section.init_db = types.MethodType(init_db, admin_section)

