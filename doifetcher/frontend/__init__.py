# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for
from jinja2 import TemplateNotFound
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from flask_wtf import Form
from wtforms import TextField, TextAreaField, HiddenField, ValidationError, SubmitField, FormField, FieldList, validators
from wtforms.validators import Required, Optional

from doifetcher.forms import *

frontend = Blueprint(u'Simple GUI', __name__, template_folder='templates')

def validate_doi(doi):
    return True # Currently everything goes

@frontend.route('/')
def welcome_page():
        form = AddArticleForm()
        form.validate_on_submit()
        return render_template('index.html', form=form) 

@frontend.route('/add', methods=['GET', 'POST'])
@frontend.route('/add/<path:doi>', methods=['GET', 'POST'])
def add(doi=None):
        form = AddArticleForm()
        if (form.validate_on_submit()): # Save data into DB
                return u"Saving data into DB"
        else: # Showing the add form

                if (doi is not None):
                        import requests
                        import json
                        url = "http://dx.doi.org/"
                        headers = {'Accept': 'frontendlication/vnd.citationstyles.csl+json;q=1.0'}
                        if validate_doi(doi):
                                form.doi_field.data = doi
                                req = requests.get("{}{}".format(url,doi), headers=headers)
                                if (req.status_code == requests.codes.ok): # Got a response
                                        form.doi_field.flags.valid = True
                                        # Now populate other field
                                        json_data = req.json()
                                        if (json_data[u'author']):
                                                authors_txt = u""
                                                for author in json_data[u'author']:
                                                        if (author[u'family'] and author[u'given']):
                                                                authors_txt += u"{last}, {firsts}\n".format(last=author[u'family'], firsts=author[u'given'])
                                                form.authors_field.data = authors_txt
                                        if (json_data[u'container-title']):
                                                form.journal_field.data = json_data[u'container-title']
                                        if (json_data[u'title']):
                                                form.title_field.data = json_data[u'title']
                                        if (json_data[u'volume']):
                                                form.volume_field.data = json_data[u'volume']                   
                                        if (json_data[u'page']):
                                                form.pages_field.data = json_data[u'page']
                                        if (json_data[u'indexed']):
                                                indexed = json_data[u'indexed']
                                                if (indexed[u'date-parts']):
                                                        form.year_field.data = indexed[u'date-parts'][0][0]
                                else: # Did not receive a proper response
                                        form.doi_field.errors = u'DOI invalid'
                                        form.doi_field.flags.valid = False     


                        return render_template('add.html', form=form)                       
                else:
                        #form = AddArticleForm()
                        #form.validate_on_submit() # get error messages to the browser
                        return render_template('add.html', form=form)               


