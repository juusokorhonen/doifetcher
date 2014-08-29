# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
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
import requests
import json
import unicodedata
import re
import codecs

simple = Blueprint(u'simple', __name__, template_folder='templates', static_folder='static', static_url_path='/static/simple')

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

def apply_unicode_tricks(json_data):
    json_str = json.dumps(json_data)
    json_str.decode('unicode_escape')
    return json.loads(json_str)

def abbreviate_journal_name(name, reverse=False):
    abbreviation_dir = u"{}/{}".format(simple.root_path,'journal_abbreviations')
    abbreviation_filenames = ['journal_abbreviations_general.txt',
                                'jabref.wos.txt',
                                'journal_abbreviations_geology_physics.txt',
                                'journal_abbreviations_ieee.txt',
                                'journal_abbreviations_ams.txt',
                                'journal_abbreviations_mechanical.txt',
                                'journal_abbreviations_meteorology.txt',
                                'journal_abbreviations_sociology.txt',
                                'journal_abbreviations_medicus.txt',
                                'journal_abbreviations_entrez.txt']
    for filename in abbreviation_filenames: # Try all abbreviation files one by one
        # This load trick from http://stackoverflow.com/questions/4842057/python-easiest-way-to-ignore-blank-lines-when-reading-a-file
        # Code borrowed from bibbreviate package by Steven Hamblin (https://github.com/Winawer/bibbreviate)
        try:
            abbrevs = filter(None,(line.rstrip() for line in codecs.open(u"{}/{}".format(abbreviation_dir,filename),encoding='utf-8')))
        except:
            print(u"Could not open file: {}".format(filename))
            continue # If we could not open the file, then continue
        abbrevs = [ line.split('=') for line in abbrevs if line[0] != u"#" ]
        try:
            abbrevs = [ [line[0].strip(),line[1].strip()] for line in abbrevs ]
        except:
            print(u"Parsing file {} failed due to index of of bounds.".format(filename))
            print(u"Parsed line was: {}".format(line))
            continue
        if not reverse:
            abbrevs = { line[0].strip().lower():line[1].strip() for line in abbrevs}
        else:
            abbrevs = { line[1].strip().lower():line[0].strip() for line in abbrevs}
        # Now we have abbreviations in abbrevs list
        if len(name.split(' ')) > 1: # This means that the journal name has more than one part (ie. it's not "Nature")
            journal = name.lower()
            # Handle any difficult characters. TODO: check that this list is complete.
            journal_clean = re.sub('[{}]','',journal)
            try:
                abbreviation = abbrevs[journal_clean]
                # If KeyError has not occurred then we found an abbreviation!
                return abbreviation # We can now exit!
            except KeyError:
                pass
                # Did not find an abbreviation so move on to the next file
        else: # No need to abbreviate!
            return name
    # We got to the end and no abbreviations were found...so return None
    return None 

@simple.route('/add', methods=['GET', 'POST'])
def add():
    form = AddArticleForm()

    if (request.method == 'POST'): # Requested to save the form
        if (form.fetch_doi.data): # Fetch DOI
            json_data = fetchDOIData(form.doi_field.data)
            json_data = apply_unicode_tricks(json_data)

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
                    author = Author(**hn.as_dict(True))
                    possible_matches = Author.query.filter_by(last=author.last, first=author.first)
                    # TODO: If author only provides initials, then try to match those
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
                    abbrev = abbreviate_journal_name(journal_input)
                    if abbrev is not None:
                        journal.abbreviation = abbrev
                    else:
                        # Abbreviation turned out None, which could mean that it is not in the database or that the provided journal name is already an
                        # abbreviation! We test this by running the process in reverse.
                        fullname = abbreviate_journal_name(journal_input, reverse=True)
                        if fullname is not None:
                            journal.name = fullname
                            journal.abbreviation = journal_input
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
                doi = doi if doi != u"" else None
                title = title if title != u"" else None
                volume = volume if volume != u"" else None
                pages = pages if pages != u"" else None
                year = year if year != u"" else None
                json_data = json_data if json_data != u"" else None

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
                        try:
                            json_year = date_data[0][0]
                            json_month = date_data[0][1]
                            json_day = date_data[0][2]
                        except IndexError:
                            if not 'json_year' in locals():
                                json_year = year
                            if not 'json_month' in locals():
                                json_month = 1
                            if not 'json_day' in locals():
                                json_day = 1
                        if (int(json_year) == int(year)):
                            pub_date = datetime(int(json_year), int(json_month), int(json_day))
                        else:
                            # ie. the user has modified the year input, now use a default of Jan 1st
                            pub_date = datetime(int(year), 1, 1)
                else:
                    try:
                        pub_date = datetime(int(year), 1, 1)
                    except:
                        pub_date = None 


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
                            authors=[author for (author,new) in authors]) # author contains tuples of the form: (author, new)
                    if json_data:
                        article.json_data=json.dumps(json_data)

                    db.session.add(article)
                else: # Article found in database
                    #flash(u"Article already in database, updating fields", 'info')
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
                    
                    newauthors = [author for (author, new) in authors if new]
                    allauthors = [author for (author, new) in authors]
                    authorsmsg = u""
                    for author in article.authors:
                        # Remove obsoleted authors
                        if author not in allauthors:
                            if authorsmsg != u"": authorsmsg += u", " # Add a comma to the list
                            authorsmsg += "- {}".format(author.name())
                    for author in newauthors:
                        # Insert new authors
                        if authorsmsg != u"": authorsmsg += u", " # Add a comma to the list
                        authorsmsg += u"+ {}".format(author.name())
                    article.authors = allauthors

                    if authorsmsg != u"":
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
                        updatemsg += u"authors modified: {}".format(authorsmsg)
                    
                    if (article.json_data != json.dumps(json_data)):
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
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
                        flash(u"Article already in database.\nNo fields updated", 'info')
                    else:
                        flash(u"Article already in database.\nUpdated fields: {}".format(updatemsg), 'info')
                
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
