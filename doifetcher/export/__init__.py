# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound
from flask_bootstrap import Bootstrap
from doifetcher.model import Article, Author, Journal

export = Blueprint(u'export', __name__, template_folder='templates', static_folder='static', static_url_path='/static/export')

def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return (best == 'application/json') and (request.accept_mimetypes[best] > request.accept_mimetypes['text/html'])

@export.route('/export', methods=['GET'])
def export_welcome():
    try:
        return render_template('export.html')
    except TemplateNotFound:
        abort(404)

@export.route('/export/all', methods=['GET'])
def export_all():
    # We put all the data in the list "articles" and give it out to the template
    articles = Article.query.order_by(Article.pub_date).all()
    #for article in articles:
    #    print(article.title.encode('utf-8'))
    #    for author in article.authors:
    #        print(author.last.encode('utf-8'))
    try:
        if (request_wants_json()):
            return jsonify(articles)
        else:
            export_formatter = u'list_ordered_by_year.html'
            try:
                exportformat = request.args.get('format', '')
                if (exportformat == u'text_by_author'):
                    export_formatter = u'text_ordered_by_author.html'
            except KeyError:
                pass
            # Render the list
            listhtml = render_template(export_formatter, articles=articles)
            return render_template('export_all.html', listhtml=listhtml)
    except TemplateNotFound:
        abort(404)
