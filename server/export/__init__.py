# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound
from flask_bootstrap import Bootstrap
from database.model import Article, Author, Journal
import datetime

export = Blueprint(u'export', __name__, template_folder='templates', static_folder='static', static_url_path='/static/export')

def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return (best == 'application/json') and (request.accept_mimetypes[best] > request.accept_mimetypes['text/html'])

@export.route('/export', methods=['GET'])
def export_welcome():
    return redirect(url_for('.export_all'))
    try:
        return render_template('export.html')
    except TemplateNotFound:
        abort(404)

def render_with_format(query, **kwargs):
    """
    Helper function to wrap all export routes.
    """
    default_format = 'interactive_html'
    export_format = request.args.get('format', default_format)
    if (query.count() == 0):
        # No articles found
        flash("No articles found!")
        articles=[]
    else:
        articles = query.all()

    try:
        return render_template(export_format + '.html', articles=articles, **kwargs)
    except TemplateNotFound:
        if current_app.debug:
            print("Requested formatter not found : {}".format(export_format))
        flash("Formatter not found!", category='error')
        return render_template('export_all.html', articles=articles, **kwargs)

@export.route('/export/all', methods=['GET'])
def export_all():
    # We put all the data in the list "articles" and give it out to the template
    query = Article.query.order_by(Article.pub_date)
    return render_with_format(query) 

@export.route('/export/author/<int:author_id>', methods=['GET'])
def export_by_author(author_id):
    try:
        author = Author.query.get(author_id)
    except Exception as e:
        if current_app.debug:
            print("Fetching author (id={}) failed . {}".format(author_id, str(e)))
        return abort(404)
    if author is None:
        if current_app.debug:
            print("Author id {} not found.".format(author_id))
        return abort(404)
   
    query = Article.query.filter(Article.authors.any(id=author_id))
    
    filters = {}

    try:
        # See if we have a year
        year = int(request.args['year'])
        start_date = datetime.datetime(year,1,1)
        end_date = datetime.datetime(year,12,31)

        query = query.filter(Article.pub_date > start_date, Article.pub_date < end_date)
        filters['year'] = {'id': year, 'name': year, 'field': 'year'}
    except:
        pass

    try:
        # See if we have a journal
        journal_id = int(request.args['journal_id'])
        
        journal = Journal.query.get(journal_id)
        query = query.filter_by(journal_id=journal_id)
        filters['journal'] = {'id': journal_id, 'name': journal.name, 'field': 'journal_id'}
    except:
        pass

    query = query.order_by(Article.pub_date)

    return render_with_format(query, filters=filters, author=author.name())

@export.route('/export/journal/<int:journal_id>', methods=['GET'])
def export_by_journal(journal_id):
    try:
        journal = Journal.query.get(journal_id)
    except Exception as e:
        if current_app.debug:
            print("Fetching journal (id={}) failed . {}".format(journal_id, str(e)))
        return abort(404)
    if journal is None:
        if current_app.debug:
            print("Journal id {} not found.".format(journal_id))
        return abort(404)

    query = Article.query.filter_by(journal_id=journal_id).order_by(Article.pub_date)
    filters = {}

    return render_with_format(query, filters=filters, journal=journal.name)

@export.route('/export/year/<int:year>', methods=['GET'])
def export_by_year(year):
    try:
        year = int(year)
    except:
        if current_app.debug:
            print("Could not transform {} into a year.".format(year))
        abort(404)

    start_date = datetime.datetime(year,1,1)
    end_date = datetime.datetime(year,12,31)

    query = Article.query.filter(Article.pub_date > start_date, Article.pub_date < end_date).order_by(Article.pub_date)
    filters = {}

    return render_with_format(query, filters=filters, year=year)
