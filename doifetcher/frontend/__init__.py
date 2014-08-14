# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for
from jinja2 import TemplateNotFound
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
from flask_wtf import Form
from wtforms import TextField, TextAreaField, HiddenField, ValidationError, SubmitField, FormField, FieldList, validators
from wtforms.validators import Required, Optional
import re
from doifetcher.forms import *
from doifetcher.model import *

frontend = Blueprint(u'Simple GUI', __name__, template_folder='templates')

def validate_doi(doi):
    doi_validator = re.compile("(^$|(doi:)?10\.\d+(.\d+)*/.*)")
    return doi_validator.match(doi) # Check if doi matches 

def fetchDOIData(doi):
    """Takes a doi as an argument and returns a JSON representation of the article."""

    doi = doi.strip() # Get rid of whitespace
    
    if not validate_doi(doi):
        flash("DOI appers to be invalid. Please check your input.", 'warning')
        return None
    
    import requests
    import json
    url = "http://dx.doi.org/"
    headers = {'Accept': 'application/vnd.citationstyles.csl+json;q=1.0'}
    req = requests.get("{}{}".format(url,doi), headers=headers)
    
    if (req.status_code != requests.codes.ok):
        # Request failed
        if (req.status_code == 204): 
            errormsg = u"No metadata available"
        elif (req.status_code == 404):
            errormsg = u"The requested DOI does not exist"
        elif (req.status_code == 406): 
            errormsg = u"Cannot serve the requested content type"
        else:
            errormsg = u"Unknown status code {}".format(req.status_code)
        flash(u"DOI fetch failed: {}".format(errormsg), 'warning')
        return None
    
    # Request ok, so process json
    try: 
        json_data = req.json()
    except ValueError, ve:
        flash("Something went wrong: Parsing article data failed.", 'warning')
        return None
    
    return json_data

@frontend.route('/')
def index():
        form = AddArticleForm()
        return render_template('index.html', form=form) 

@frontend.route('/add', methods=['GET', 'POST'])
def add():
    form = AddArticleForm()

    if (request.method == 'POST'): # Requested to save the form
        if (form.fetch_doi.data): # Fetch DOI
            json_data = fetchDOIData(form.doi_field.data)

            # Now process the json data into the form
            if (json_data):
                form.doi_field.flags.valid = True
                form.json_field.data = json_data
                #authors_txt = u""
                # Empty the authors fieldlist
                while (len(form.authors_fieldlist) > 0):
                    form.authors_fieldlist.pop_entry() 
                for author in json_data.get(u'author'):
                    if (author.get(u'family') and author.get(u'given')):
                        #authors_txt += u"{last}, {firsts}\n".format(last=author[u'family'], firsts=author[u'given'])
                        form.authors_fieldlist.append_entry({'firstname':author[u'given'],'lastname':author[u'family']})
                #form.authors_field.data = authors_txt
                form.journal_field.data = json_data.get(u'container-title')
                form.title_field.data = json_data.get(u'title')
                form.volume_field.data = json_data.get(u'volume')                   
                form.pages_field.data = json_data.get(u'page')
                indexed = json_data.get(u'indexed')
                date_data = indexed.get(u'date-parts') 
                if (date_data):
                    form.year_field.data = date_data[0][0] 
            return render_template('add.html', form=form)  

        elif (form.save.data): # Save article to database
            if (form.validate()): # If form validates, save it        
                # Process authors
                authors = []
                while (len(form.authors_fieldlist) > 0):
                    author_data = form.authors_fieldlist.pop_entry()
                    authors.append(Author(author_data[u'firstname'],author_data[u'lastname']))
                # Add authors into the database
                for author in authors:
                    # Check if the author already exists in the database
                    pass        
                return render_template('save.html', form=form)            
            else: # Requested save, but form did not validate
                flash('There were errors in the form', 'error')
                print(form.errors)
                return render_template('add.html', form=form)

        else: # Posted something, but did not press fetchdoi or save
            flash(u"Uknown error occurred", 'error')
            return render_template('add.html', form=form)

    else: # Request method is GET, so show the form
        return render_template('add.html', form=form)
