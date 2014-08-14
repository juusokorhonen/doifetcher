# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask_wtf import Form
import wtforms
from wtforms import StringField, TextAreaField, HiddenField, ValidationError, SubmitField, FormField, FieldList, validators
from wtforms.validators import Required, Optional, Regexp
import re

class AuthorForm(wtforms.Form):
    firstname = StringField(u"First name", validators=[Required()])
    lastname = StringField(u"Last name", validators=[Required()])
    class Meta:
        csrf = False

class AddArticleForm(Form):
    doi_field = StringField(u"DOI", validators=[Optional()])
    #authors_field = TextAreaField(u"Authors", description=u"Add one author per line in the form, eg. \"Crick, J. D.\"", validators=[Required()])
    authors_fieldlist = FieldList(FormField(AuthorForm), min_entries=1, label=u"Authors")
    journal_field = StringField(u"Journal", validators=[Required()])
    title_field = StringField(u"Title", validators=[Required()])
    volume_field = StringField(u"Volume", validators=[Optional()])
    pages_field = StringField(u"Pages", validators=[Optional()])
    year_field = StringField(u"Year", validators=[Required()])
    json_field = HiddenField(u"JSON data", validators=[Optional()])
    fetch_doi = SubmitField()
    save = SubmitField()
