# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound
from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from doifetcher.model import Article, Author, Journal

admin_section = Admin()

class _AdminView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

# Test view
admin_section.add_view(_AdminView('Hello'))

class _DbView(ModelView):
    can_create = False
    
    # Excluded columns
    column_exclude_list = ['mod_date', 'add_date']

    def __init__(self, model, session, **kwargs):
        super(_DbView, self).__init__(model, session, **kwargs)
        # Override certain columns
        #column_list = self.get_list_columns()
        #print(column_list)
        #self.column_list = [key for (key,value) in column_list if (key not in self.excluded_columns)]
        #print(self.column_list)
        print(self.get_list_columns())

class _ArticleDbView(_DbView):
    pass

class _AuthorDbView(_DbView):
    pass

class _JournalDbView(_DbView):
    pass

import types
# Initialize database connection
def init_db(self, db):
    self.add_view(_ArticleDbView(Article, db.session))
    self.add_view(_AuthorDbView(Author, db.session))
    self.add_view(_JournalDbView(Journal, db.session))

admin_section.init_db = types.MethodType(init_db, admin_section)
