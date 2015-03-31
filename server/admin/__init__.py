# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound
from flask.ext.superadmin import Admin, BaseView, expose, model
#from flask.ext.superadmin.contrib.sqla import ModelView
from database.model import Article, Author, Journal

admin_section = Admin()

class _AdminView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

class _DbModel(model.ModelAdmin):
    pass

class _JournalModel(_DbModel):
    list_display = ('name', 'abbreviation', 'articles')

import types
# Initialize database connection
def init_db(self, db):
    self.register(Article, _DbModel, session=db.session)
    self.register(Author, _DbModel, session=db.session)
    self.register(Journal, _JournalModel, session=db.session)

# Bind the method to the object
admin_section.init_db = types.MethodType(init_db, admin_section)
