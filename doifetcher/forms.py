# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask_wtf import Form
import wtforms
from wtforms import StringField, TextAreaField, IntegerField, HiddenField, ValidationError, SubmitField, FormField, FieldList, validators
from wtforms.validators import Required, Optional, Regexp
import re

class AuthorForm(wtforms.Form):
    firstname = StringField(u"First name", validators=[Required()])
    middlename = StringField(u"Middle name(s)", validators=[Optional()])
    lastname = StringField(u"Last name", validators=[Required()])
    class Meta:
        csrf = False

class JournalForm(wtforms.Form):
    journalname = StringField(u"Journal name", validators=[Required()])
    abbrev = StringField(u"Abbreviation", validators=[Optional()])
    class Meta:
        csrf = False

class DateForm(wtforms.Form):
    year = StringField(u'Year', validators=[Required()])
    month = StringField(u'Month', validators=[Optional()])
    day = StringField(u'Day', validators=[Optional()])
    class Meta:
        csrf = False

class AddArticleForm(Form):
    doi_field = StringField(u"DOI", validators=[Optional()])
    #authors_field = TextAreaField(u"Authors", description=u"Add one author per line in the form, eg. \"Crick, J. D.\"", validators=[Required()])
    authors_fieldlist = FieldList(FormField(AuthorForm), min_entries=1, label=u"Authors")
    #journal_field = StringField(u"Journal", validators=[Required()])
    journal_field = FormField(JournalForm) 
    title_field = StringField(u"Title", validators=[Required()])
    volume_field = StringField(u"Volume", validators=[Optional()])
    pages_field = StringField(u"Pages", validators=[Optional()])
    #year_field = StringField(u"Year", validators=[Required()])
    date_field = FormField(DateForm)
    json_field = HiddenField(u"JSON data", validators=[Optional()])
    fetch_doi = SubmitField()
    save = SubmitField()
