# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound

browse = Blueprint(u'browse', __name__, template_folder='templates', static_folder='static', static_url_path='/static/browse')

@browse.route('/browse', methods=['GET'])
def browse_articles():
    try:
        return render_template('browse.html')
    except TemplateNotFound:
        abort(404)
