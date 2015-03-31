# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound
from flask_bootstrap import Bootstrap
from database.model import Article, Author, Journal

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
            listhtml = render_template('list_ordered_by_year.html', articles=articles)
            return render_template('export_all.html', listhtml=listhtml)
    except TemplateNotFound:
        abort(404)
