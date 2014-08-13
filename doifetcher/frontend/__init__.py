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
def index():
        form = AddArticleForm()
        form.validate_on_submit()
        return render_template('index.html', form=form) 

@frontend.route('/add', methods=['GET', 'POST'])
def add():
    form = AddArticleForm(request.form)
    if (form.save.data): # Save data into DB
        if (form.validate_on_submit()):
            return u"Saving data into DB"
        else:
            flash(u"Errors in form input", 'error')
            return render_template('add.html', form=form)
    elif (form.fetchdoi.data): # Fetch DOI
        if (request.method == 'POST' and form.doi_field.data is not None):
            doi = form.doi_field.data.strip()
            import requests
            import json
            url = "http://dx.doi.org/"
            headers = {'Accept': 'application/vnd.citationstyles.csl+json;q=1.0'}
            if validate_doi(doi):
                form.doi_field.data = doi
                req = requests.get("{}{}".format(url,doi), headers=headers)
                if (req.status_code == requests.codes.ok): # Got a response
                    # Now populate other field
                    try:
                        json_data = req.json()
                    except ValueError, ve:
                        flash(u"Parsing JSON data failed. No pre-fetched data available.", 'warning')
                    else:
                        form.doi_field.flags.valid = True
                        authors_txt = u""
                        for author in json_data.get(u'author'):
                            if (author.get(u'family') and author.get(u'given')):
                                authors_txt += u"{last}, {firsts}\n".format(last=author[u'family'], firsts=author[u'given'])
                                form.authors_field.data = authors_txt
                        form.journal_field.data = json_data.get(u'container-title')
                        form.title_field.data = json_data.get(u'title')
                        form.volume_field.data = json_data.get(u'volume')                   
                        form.pages_field.data = json_data.get(u'page')
                        indexed = json_data.get(u'indexed')
                        date_data = indexed.get(u'date-parts') 
                        if (date_data):
                            form.year_field.data = date_data[0][0] 
                else: # Did not receive a proper response
                    if (req.status_code == 204): 
                        errormsg = u"No metadata available"
                    elif (req.status_code == 404):
                        errormsg = u"The requested DOI does not exist"
                    elif (req.status_code == 406): 
                        errormsg = u"Cannot serve the requested content type"
                    else:
                        errormsg = u"Unknown status code {}".format(req.status_code)
                        flash(u"DOI fetch failed: {}".format(errormsg), 'error')
                        form.doi_field.errors = u'DOI invalid'
            else:
                flash("Incomplete request", 'warning')
        return render_template('add.html', form=form)                       
    else: 
        flash("DEBUG: Default request")
        return render_template('add.html', form=form)               

