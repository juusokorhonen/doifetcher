# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound
from flask_bootstrap import Bootstrap
from database.model import Article, Author, Journal, db
import datetime

export = Blueprint(u'export', __name__, template_folder='templates', static_folder='static', static_url_path='/static/export')

def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return (best == 'application/json') and (request.accept_mimetypes[best] > request.accept_mimetypes['text/html'])

def render_with_format(query, **kwargs):
    """
    Helper function to wrap all export routes.
    """
    default_format = 'interactive_html'
    export_format = request.args.get('format', default_format)
    if (query.count() == 0):
        # No articles found
        #flash("No articles found!")
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

def get_year_range():
    query = db.session.query(db.func.max(Article.pub_date).label('max_date'), db.func.min(Article.pub_date).label('min_date'))
    result = query.one()
    min_year = result.min_date.year
    max_year = result.max_date.year
    return range(min_year, max_year+1)

def apply_filters(query=None, filters={}, order_by=None):
    if current_app.debug:
        print("apply_filters() called, with requst.args:")
        for key,vals in request.args.to_dict(flat=False).items():
            print("{} : {}".format(key, vals))
            for val in vals:
                print("{} : {}".format(" "*len(key), val))

    if query is None:
        query = Article.query

    try:
        # See if we have a year
        years = [int(i) for i in request.args.getlist('year')]
        if current_app.debug:
            print("Years:")
            for year in years:
                print(year)

        for year in years:
            start_date = datetime.datetime(year,1,1)
            end_date = datetime.datetime(year,12,31)
            
            # TODO: This part puts AND requirements and we need OR
            query = query.filter(Article.pub_date > start_date, Article.pub_date < end_date)
            filters['year'] = {'id': year, 'name': year, 'field': 'year'}

    except Exception as e:
        if current_app.debug:
            print("Filtering by date failed: {}".format(str(e)))

    try:
        # See if we have a journal
        journal_id = int(request.args['journal_id'])
        
        journal = Journal.query.get(journal_id)
        query = query.filter_by(journal_id=journal_id)
        filters['journal'] = {'id': journal_id, 'name': journal.name, 'field': 'journal_id'}
    except:
        pass

    try:
        # See if we have a authors
        author_ids = [int(v) for k,v in request.args.items() if k == 'author_id']
        if (len(author_ids) == 0):
            pass
        elif (len(author_ids) == 1):
            # One author
            author = Author.query.get(author_ids[0])
            query = query.filter(Article.authors.any(id=author_ids[0]))
            filters['author'] = {'id': author_ids[0], 'name': author.name(), 'value': author, 'field': 'author_id'}
        else:
            # Multiple authors
            authors = Author.query.filter(id.in_(author_ids)).all()
            query = query.filter(Article.authors.any.in_(author_ids))
            filters['author'] = []
            for author in authors:
                filters['author'].append({'id': author.id, 'name': author.name(), 'value': author, 'field': 'author_id'})
    except Exception as e:
        if current_app.debug:
            print("No author filters found: {}".format(str(e)))

    # Order the query
    if order_by is None:
        query = query.order_by(Article.pub_date)
    else:
        raise NotImplementedError

    return (query, filters)

@export.route('/export', methods=['GET'])
def export_all():
    # We put all the data in the list "articles" and give it out to the template
    (query, filters) = apply_filters() 
    return render_with_format(query, years=get_year_range(), filters=filters) 

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
    (query, filters) = apply_filters(query=query)

    return render_with_format(query, filters=filters, author=author, years=get_year_range())

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

    query = Article.query.filter_by(journal_id=journal_id)
    (query, filters) = apply_filters(query=query)

    return render_with_format(query, filters=filters, journal=journal, years=get_year_range())

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
    (query, filters) = apply_filters(query=query) 

    return render_with_format(query, filters=filters, year=year, years=get_year_range())
