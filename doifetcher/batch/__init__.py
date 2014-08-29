# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound
from flask_bootstrap import Bootstrap

batch = Blueprint(u'batch', __name__, template_folder='templates', static_folder='static', static_url_path='/static/batch')

@batch.route('/batch', methods=['GET'])
def batch_import():
    try:
        return render_template('batch.html')
    except TemplateNotFound:
        abort(404)

