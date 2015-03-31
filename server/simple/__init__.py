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
from server.forms import *
from database.model import *
import database.model as model
from datetime import datetime
import requests
import json
import unicodedata
import re
import codecs
from nameparser import HumanName
import chardet

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
    #print("Encoding: {}".format(req.encoding))
    #req.encoding = 'utf-8'
    #print("Encoding: {}".format(req.encoding))
    #print("Content (type: {}): {}".format(type(req.content), req.content))

    # Request ok, so process json
    try: 
        #print(u"Text (type {}): {}".format(type(req.text), req.text))
        unicodestr = apply_unicode_tricks(req.text)
        #print(u"Unicode text (type {}): {}".format(type(unicodestr), unicodestr))
        json_data = json.loads(unicodestr, encoding='utf-8')
    except ValueError, ve:
        flash("Something went wrong: Parsing article data failed.", 'warning')
        return None
    
    return json_data

def apply_unicode_tricks(rawstr):
    """Returns an unicode representation of the rawdata."""
    try:
        unicodestr = unicode(rawstr)
    except TypeError:
        # We already had unicode
        unicodestr = rawstr 
    # Try to unescape unicode
    try:
        unicodestr = unicodestr.decode('unicode_escape')
    except UnicodeEncodeError:
        pass # Nothing to escape
    # Now normalize to Normal Form C, which seems to work best with Google Fonts (NFD fails for some reason) 
    unicodestr = unicodedata.normalize(u'NFC', unicodestr)
    return unicodestr

def abbreviate_journal_name(name, reverse=False):
    """Returns the abbreviation of the provided journal name.
       Reverse option allows to find the full name based on abbreviation.
       Return None if no match was found."""
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
        # Code gratefully borrowed from bibbreviate package by Steven Hamblin (https://github.com/Winawer/bibbreviate)
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

def expand_journal_name(name):
    """Takes a journal name (or abbreviation) as input and returns a tuple, where
       the first field is the full name and second is the possible abbreviation.
       Also tries to autodetect, if actually an abbreviation was supplied and acts
       accordingly. The abbreviation is null if no match was found."""
    abbrev = abbreviate_journal_name(name)
    if abbrev is not None:
        return (name, abbrev)
    else:
        # Abbreviation turned out None, which could mean that it is not in the database or that the provided journal name is already an
        # abbreviation! We test this by running the process in reverse.
        fullname = abbreviate_journal_name(name, reverse=True)
        if fullname is not None:
            return (fullname, name)
    # Abbreviation failed
    return (name, None)

@simple.route('/add', methods=['GET', 'POST'])
def add():
    form = AddArticleForm()

    if (request.method == 'POST'): # Requested to save the form
        if (form.fetch_doi.data): # Fetch DOI
            json_data = fetchDOIData(form.doi_field.data)

            # Now process the json data into the form
            if (json_data):
                # Process the json data
                form.doi_field.data = json_data.get(u'DOI', form.fetch_doi.data) # Update doi or use the provided one
                form.doi_field.flags.valid = True
                form.json_field.data = json.dumps(json_data, encoding='utf-8')
                #authors_txt = u""
                # Empty the authors fieldlist
                while (len(form.authors_fieldlist) > 0):
                    form.authors_fieldlist.pop_entry() 
                for author in json_data.get(u'author'):
                    if (author.get(u'family') and author.get(u'given')):
                        #authors_txt += u"{last}, {firsts}\n".format(last=author[u'family'], firsts=author[u'given'])
                        author_hn = HumanName(u"{}, {}".format(author[u'family'], author[u'given']))
                        form.authors_fieldlist.append_entry({u'firstname':author_hn.first,u'middlename':author_hn.middle,u'lastname':unicode(author_hn.last)})
                # Work out the journal name and abbreviation from the json data
                (journal_fullname, journal_abbrev) = expand_journal_name(json_data.get(u'container-title'))
                form.journal_field.journalname.data = journal_fullname 
                if journal_abbrev is not None:
                    form.journal_field.abbrev.data = journal_abbrev
                # Work out title, volume, pages
                form.title_field.data = json_data.get(u'title')
                form.volume_field.data = json_data.get(u'volume')                   
                form.issue_field.data = json_data.get(u'issue')
                form.pages_field.data = json_data.get(u'page')
                # Work out the publication date
                issued = json_data.get(u'issued')
                date_data = issued.get(u'date-parts') 
                if (date_data):
                    try:
                        form.date_field.year.data = date_data[0][0]
                        form.date_field.month.data = date_data[0][1]
                        form.date_field.day.data = date_data[0][2]
                    except Exception as e:
                        pass
            # Finally show the pre-filled form
            return render_template('add.html', form=form)  

        elif (form.save.data): # Save article to database
            if (form.validate()): # If form validates, save it        
                # Process authors
                authors = []
                #print(len(form.authors_fieldlist))
                while (len(form.authors_fieldlist) > 0):
                    # Process authors into the database format
                    author_form = form.authors_fieldlist.pop_entry()
                    #print(author_form)
                    author_data = {u'first': author_form.firstname.data, u'middle': author_form.middlename.data, u'last': author_form.lastname.data}
                    #print(author_data)
                    author = Author(**author_data)
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
                # However, the authors were popped out from back-to-front, thus reverse the list
                authors.reverse()
                #print(authors)
                # still required to do db.commit
    
                # Process journal
                journal_input = form.journal_field.journalname.data
                journal_input_abbrev = form.journal_field.abbrev.data
                if (journal_input_abbrev == u""):
                    journal_input_abbrev = None
                # Find out wheter journal is aleady in the database
                journal = Journal.query.filter_by(name=journal_input).first()
                if journal is None and journal_input_abbrev is not None:
                    # If journal name did not find anything and the abbreviation is set, then check also that
                    journal = Journal.query.filter_by(abbreviation=journal_input_abbrev).first()
                if journal is None:
                    # If journal not in database, create one and add it there
                    journal = Journal(name=journal_input, abbreviation=journal_input_abbrev)
                    db.session.add(journal)
                # journal now contains the journal for this article and the possibly new journal has been added to the database (waiting for db.session.commit)

                # Process article
                doi = form.doi_field.data
                title = form.title_field.data
                volume = form.volume_field.data
                issue = form.issue_field.data
                pages = form.pages_field.data
                year = form.date_field.year.data
                month = form.date_field.month.data
                day = form.date_field.day.data
                
                # json
                json_data = form.json_field.data

                # Make some fields None if they are empty
                doi = doi if doi != u"" else None
                title = title if title != u"" else None
                volume = volume if volume != u"" else None
                issue = issue if issue != u"" else None
                pages = pages if pages != u"" else None
                year = year if year != u"" else None
                month = month if month != u"" else None
                day = day if day != u"" else None
                try:
                    json_data = json.loads(json_data) if json_data != u"" else None
                except ValueError:
                    # Could not load json_data into json (probably it's not json)
                    json_data = None

                # Process date
                try:
                    # Process dates into numbers
                    year = int(year)
                    month = int(month)
                    day = int(day)
                except Exception as e:
                    pass
                    #print(e.__class__.__name__)
                    #print(e)
                finally:
                    if (type(year) != int):
                        year = datetime.date.today().year # Default to this year
                    if (type(month) != int or month < 1 or month > 12):
                        month = 1
                    if (type(day) != int or day < 1 or day > 31):
                        day = 1
                # Now we have year, month, day, which are all integer
                try:
                    pub_date = datetime(year, month, day)
                except ValueError:
                    # Day was probably out of bounds, since other have been checked already
                    pub_date = datetime(year, month, 1) # Default to first day of month
   
                # Check whether the doi already exists in the database
                article = None # Have to initialize this way so that second if-clause doesn't return with error
                if doi is not None:
                    article = Article.query.filter_by(doi=doi).first()
                if article is None and title is not None:
                    # If doi is None, then try to fetch by article title (more unreliable due to different spelling forms)
                    article = Article.query.filter_by(title=title).first()

                # If article was not found in the database
                if article is None:
                    add_date = datetime.now()
                    article = Article(
                            doi=doi,
                            title=title,
                            volume=volume,
                            issue=issue,
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

                    if (article.issue != issue):
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
                        updatemsg += u"issue: {} --> {}".format(article.issue, issue)
                        article.issue = issue
                    
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
                    
                    if (json_data is not None and article.json_data != json.dumps(json_data)):
                        if (updatemsg != u""): updatemsg += u", " # Add a comma
                        if article.json_data is None:
                            updatemsg += u"json data added"
                            article.json_data = json.dumps(json_data)
                        else:
                            updatemsg += u"json data modified"

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
            flash(u"Unknown error occurred", 'error')
            return render_template('add.html', form=form)

    else: # Request method is GET, so show the form
        return render_template('add.html', form=form)
