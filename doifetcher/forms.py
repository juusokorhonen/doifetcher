# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask_wtf import Form
from wtforms import TextField, TextAreaField, HiddenField, ValidationError, SubmitField, FormField, FieldList, validators
from wtforms.validators import Required, Optional, Regexp
import re

doi_validator = Regexp("(^$|(doi:)?10\.\d+(.\d+)*/.*)", flags=re.I, message="The provided DOI is invalid - it should look similar to '10.1234/foo.bar'.")

class AddArticleForm(Form):
    doi_field = TextField(u"DOI", validators=[Required(), doi_validator])
    authors_field = TextAreaField(u"Authors", description=u"Add one author per line in the form, eg. \"Crick, J. D.\"", validators=[Required()])
    authors_fieldlist = FieldList(TextField(u"Author"), min_entries=2)
    journal_field = TextField(u"Journal", validators=[Required()])
    title_field = TextField(u"Title", validators=[Required()])
    volume_field = TextField(u"Volume", validators=[Optional()])
    pages_field = TextField(u"Pages", validators=[Optional()])
    year_field = TextField(u"Year", validators=[Required()])
    json_field = HiddenField(u"JSON data", validators=[Optional()])
    fetchdoi = SubmitField()
    save = SubmitField()
