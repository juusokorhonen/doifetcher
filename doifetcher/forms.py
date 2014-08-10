# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask_wtf import Form
from wtforms import TextField, TextAreaField, HiddenField, ValidationError, SubmitField, FormField, FieldList, validators
from wtforms.validators import Required, Optional

class AddArticleForm(Form):
	doi_field = TextField(u"DOI", validators=[Required()])
	authors_field = TextAreaField(u"Authors", description=u"Add one author per line in the form, eg. \"Crick, J. D.\"", validators=[Required()])
	authors_fieldlist = FieldList(TextField(u"Author"), min_entries=1)
	journal_field = TextField(u"Journal", validators=[Required()])
	title_field = TextField(u"Title", validators=[Required()])
	volume_field = TextField(u"Volume", validators=[Optional()])
	pages_field = TextField(u"Pages", validators=[Optional()])
	year_field = TextField(u"Year", validators=[Required()])
	submit_button = SubmitField("Save")

