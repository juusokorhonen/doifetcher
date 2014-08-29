# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, Blueprint, current_app, request, render_template, redirect, flash, url_for, abort
from jinja2 import TemplateNotFound
from flask_bootstrap import Bootstrap

export = Blueprint(u'export', __name__, template_folder='templates', static_folder='static', static_url_path='/static/export')

@export.route('/export', methods=['GET'])
def export_data():
    try:
        return render_template('export.html')
    except TemplateNotFound:
        abort(404)

