# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound
from flask_bootstrap import Bootstrap
from database.model import Article, Author, Journal, Tag, db
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
    year = datetime.date.today().year
    min_year,max_year = year,year
    if result is not None and len(result) > 0:
        if result.min_date is not None:
            min_year = result.min_date.year 
        if result.max_date is not None:
            max_year = result.max_date.year     
    return range(min_year, max_year+1)

def apply_fs(query=None, fs={}, order_by=None):
    if query is None:
        query = Article.query

    try:
        # See if we have a year
        years = [int(i) for i in request.args.getlist('year')]
        if years is not None and len(years) > 0:
            if len(years) > 1:
                query = query.filter(db.extract('year',Article.pub_date).in_(years))
                fs['year'] = [{'id': year, 'name': year, 'value': year} for year in years]
            else:
                print("Years = {}".format(str(years)))
                year = years[0]
                query = query.filter(db.extract('year',Article.pub_date)==year)
                fs['year'] = {'id': year, 'name': year, 'value': year}

    except Exception as e:
        if current_app.debug:
            print("Filtering by date failed: {}".format(str(e)))

    try:
        # See if we have a journal
        journal_id = int(request.args['journal_id'])
        
        journal = Journal.query.get(journal_id)
        query = query.filter_by(journal_id=journal_id)
        fs['journal_id'] = {'id': journal_id, 'name': journal.name, 'value': journal}
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
            fs['author_id'] = {'id': author_ids[0], 'name': author.name(), 'value': author}
        else:
            # Multiple authors
            authors = Author.query.filter(id.in_(author_ids)).all()
            query = query.filter(Article.authors.any(Author.id.in_(author_ids)))
            fs['author_id'] = []
            for author in authors:
                fs['author_id'].append({'id': author.id, 'name': author.name(), 'value': author})
    except Exception as e:
        if current_app.debug:
            print("No author fs found: {}".format(str(e)))

    try:
        # Check for tags
        tag_names = request.args.getlist('tag')
        if tag_names is not None and len(tag_names) > 0:
            if len(tag_names) > 1:
                query = query.filter(Article.tags.any(Tag.name.in_(tag_names)))
                fs['tag'] = [{'id': tag_name, 'name': tag_name, 'value': tag_name} for tag_name in tag_names]
            else:
                query = query.filter(Article.tags.any(name=tag_names[0]))
                fs['tag'] = {'id': tag_names[0], 'name': tag_names[0], 'value': tag_names[0]}
    except Exception as e:
        if current_app.debug:
            print("Filtering by tag failed: {}".format(str(e)))
        pass

    # Order the query
    if order_by is None:
        query = query.order_by(Article.pub_date)
    else:
        raise NotImplementedError

    return (query, fs)

@export.route('/export', methods=['GET'])
def export_all():
    # We put all the data in the list "articles" and give it out to the template
    fs = {}
    query = Article.query
    (query, fs) = apply_fs(query=query, fs=fs) 
    return render_with_format(query, years=get_year_range(), fs=fs) 
