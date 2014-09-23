# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound
from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from doifetcher.model import Article, Author, Journal

admin_section = Admin()

class AdminView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

# Test view
admin_section.add_view(AdminView('Hello'))

import types
# Initialize database connection
def init_db(self, db):
    self.add_view(ModelView(Journal, db.session))

admin_section.init_db = types.MethodType(init_db, admin_section)
