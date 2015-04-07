# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort, g
from jinja2 import TemplateNotFound
from flask.ext.superadmin import Admin, BaseView, expose, model, AdminIndexView
from flask.ext.superadmin.contrib.sqlamodel import ModelView
from flask.ext.login import login_required, current_user
#from flask.ext.superadmin.contrib.sqla import ModelView
from database.model import Article, Author, Journal, User


class JKAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        if current_app.debug:
            print("JKAdminView index hit.")
        return self.render('admin/index.html')

    def is_accessible(self):
        if current_app.debug:
            print("is_accessible() at JKAdminView hit with user {}".format(current_user))
        return current_user.is_authenticated()

class JKDbModel(model.ModelAdmin):
    def is_accessible(self):
        if current_app.debug:
            print("is_accessible() at JKDbModel hit with user {}".format(current_user))
        return current_user.is_authenticated()

admin_section = Admin(index_view=JKAdminView())

import types
# Initialize database connection
def init_db(self, db):
    self.register(Article, JKDbModel, session=db.session)
    self.register(Author, JKDbModel, session=db.session)
    self.register(Journal, JKDbModel, session=db.session)
    self.register(User, JKDbModel, session=db.session)

# Bind the method to the object
admin_section.init_db = types.MethodType(init_db, admin_section)

