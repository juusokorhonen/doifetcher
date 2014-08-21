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
import doifetcher.model as model
from datetime import datetime
import json

frontend = Blueprint(u'frontend', __name__, template_folder='templates', static_folder='static', static_url_path='/static/frontend')

def validate_doi(doi):
    doi_validator = re.compile("(^$|(doi:)?10\.\d+(.\d+)*/.*)")
    return doi_validator.match(doi) # Check if doi matches 

def validate_url(url):
    url_validator = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE) 
    return url_validator.match(url)

def fetchDOIData(doi):
    """Takes a doi as an argument and returns a JSON representation of the article."""

    doi = doi.strip() # Get rid of whitespace
    
    if not validate_doi(doi):
        # Try to parse, if supplied an url insted of doi
        from urlparse import urlparse
        parsed_url = urlparse(doi)
        parsed_doi = parsed_url.path[1:]
        #print(parsed_doi)
        if not validate_doi(parsed_doi):
            flash("DOI appers to be invalid. Please check your input.", 'error')
            return None
        else:
            flash("DOI was supplied in URL form. Tried to correct automatically.", 'warning')
            doi = parsed_doi
    
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
        #json_data = json.dumps(req.data)
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
                form.doi_field.data = json_data.get(u'DOI', form.fetch_doi.data) # Update doi or use the provided one
                form.doi_field.flags.valid = True
                form.json_field.data = json.dumps(json_data)
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
                issued = json_data.get(u'issued')
                date_data = issued.get(u'date-parts') 
                if (date_data):
                    form.year_field.data = date_data[0][0] 
            return render_template('add.html', form=form)  

        elif (form.save.data): # Save article to database
            if (form.validate()): # If form validates, save it        
                # Process authors
                authors = []
                while (len(form.authors_fieldlist) > 0):
                    from nameparser import HumanName
                    author_form = form.authors_fieldlist.pop_entry()
                    author_data = {'firstname': author_form.firstname.data, 'lastname': author_form.lastname.data}
                    hn = HumanName(u"{}, {}".format(author_data[u'lastname'], author_data[u'firstname'])) # HumanName parses names from strings, thus combine the already separated last and first names
                    author = Author(**hn.as_dict(False))
                    possible_matches = Author.query.filter_by(last=author.last, first=author.first)
                    found_match = None
                    for possible_match in possible_matches:
                        if (author == possible_match):
                            found_match = possible_match # TODO: this could be modified to yield a match value, higher values mean better match
                            break
                    if found_match is None:
                        authors.append((author, True)) # Second field of tuple contains information whether the author was just added to the database
                        # Insert new author into the database
                        db.session.add(author)
                    else:
                        authors.append((found_match, False))
                # authors now contains all the authors and the new ones are added to the db.session
                # still required to do db.commit
    
                # Process journal
                journal_input = form.journal_field.data
                journal = Journal.query.filter_by(name=journal_input).first()
                if journal is None:
                    # TODO: fetch journal abbreviation using ie. bibtexparser library
                    journal = Journal(name=journal_input)
                    db.session.add(journal)
                # journal now contains the journal for this article and the possibly new journal has been added to the database (waiting for db.session.commit)

                # Process article
                doi = form.doi_field.data
                title = form.title_field.data
                volume = form.volume_field.data
                pages = form.pages_field.data
                year = form.year_field.data
                
                # json
                json_data = form.json_field.data

                # Make some fields None if they are empty
                for field in [doi, title, volume, pages, year, json_data]:
                    if field == u"":
                        field = None

                # Check whether the doi already exists in the database
                if doi is not None:
                    article = Article.query.filter_by(doi=doi).first()
                elif title is not None:
                    # If doi is None, then try to fetch by article title (more unreliable due to different spelling forms)
                    article = Article.query.filter_by(title=title).first()
                
                # Fetch some extra data from json
                if json_data is not None:
                    json_data = json.loads(json_data)
                    issued = json_data.get(u'issued')
                    date_data = issued.get(u'date-parts') 
                    if (date_data):
                        json_year = date_data[0][0]
                        json_month = date_data[0][1]
                        json_day = date_data[0][2]
                        if (int(json_year) == int(year)):
                            pub_date = datetime(int(json_year), int(json_month), int(json_day))
                        else:
                            # ie. the user has modified the year input, now use a default of Jan 1st
                            pub_date = datetime(int(year), 1, 1)
                else:
                    pub_date = datetime(year, 1, 1)


                # If not then add
                if article is None:
                    add_date = datetime.now()
                    article = Article(
                            doi=doi,
                            title=title,
                            volume=volume,
                            pages=pages,
                            pub_date=pub_date,
                            add_date=add_date,
                            journal=journal,
                            authors=[author for (author,new) in authors], # author contains tuples of the form: (author, new)
                            json_data=json.dumps(json_data))

                    db.session.add(article)
                else: # Article found in database
                    flash(u"Article already in database, updating fields", 'info')
                    updatemsg = u""
                    
                    if (article.doi != doi):
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
                        updatemsg += u"DOI: {} --> {}".format(article.doi, doi)
                        article.doi = doi
                    
                    if (article.title != title):
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
                        updatemsg += u"title: {} --> {}".format(article.title, title)
                        article.title = title
                    
                    if (article.volume != volume):
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
                        updatemsg += u"volume: {} --> {}".format(article.volume, volume)
                        article.volume = volume
                    
                    if (article.pages != pages):
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
                        updatemsg += u"pages: {} --> {}".format(article.pages, pages)
                        article.pages = pages
            
                    if (article.pub_date != pub_date):
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
                        updatemsg += u"pubdate: {} --> {}".format(article.pub_date, pub_date)
                        article.pub_date = pub_date

                    if (article.journal != journal):
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
                        updatemsg += u"journal: {} --> {}".format(article.journal.name, journal.name)
                        article.journal = journal
                    
                    authorsmsg = u""
                    for author in article.authors:
                        # Remove obsoleted authors
                        if author not in authors:
                            if authormsg != u"": authorsmsg += u", " # Add a comma to the list
                            authorsmsg += "- {}".format(author.name)
                    for author in authors:
                        # Insert new authors
                        if author not in article.authors:
                            if authormsg != u"": authorsmsg += u", " # Add a comma to the list
                            authorsmsg += "+ {}".format(author.name)
                    article.authors = authors 

                    if authorsmsg != u"":
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
                        updatemsg += u"authors modified: {}".format(authorsmsg)
                    
                    if (article.json_data != json.dumps(json_data)):
                        if (updatensg != u""): updatemsg += u", " # Add a comma
                        if article.json_data is None:
                            updatemsg += u"json data modified"
                            article.json_data = json.dumps(json_data)
                        elif json_data is not None:
                            updatemsg += u"json data modified"
                            article.json_data = json.dumps(json_data)
                        else:
                            updatemsg += u"json data was preserved"

                    if (updatemsg == u""): 
                        # No fields updated
                        flash(u"Article already in database; no fields updated", 'info')
                    else:
                        flash(u"Article already in database; updated fields: {}".format(updatemsg), 'info')
                
                # Commit everything
                db.session.commit()

                return render_template('save.html', authors=authors, journal=journal, article=article)  
            else: # Requested save, but form did not validate
                flash('There were errors in the form', 'error')
                #print(form.errors)
                return render_template('add.html', form=form)

        else: # Posted something, but did not press fetchdoi or save
            flash(u"Uknown error occurred", 'error')
            return render_template('add.html', form=form)

    else: # Request method is GET, so show the form
        return render_template('add.html', form=form)
