# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, request, render_template, redirect, flash, url_for
from flask_bootstrap import Bootstrap
from flask_appconfig import AppConfig
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

def validate_doi(doi):
	return True # Currently everything goes

def create_app(configfile=None):
	app = Flask(__name__)

	AppConfig(app, configfile) # Use of flask-appconfig is highly recommended

	Bootstrap(app) # Use flask-bootstrap

	@app.route('/')
	def welcome_page():
		return render_template('index.html')	

	@app.route('/add', methods=['GET', 'POST'])
	@app.route('/add/<path:doi>', methods=['GET', 'POST'])
	def add(doi=None):
		if (request.method == 'POST'): # Save data into DB
			return u"Saving data into DB"
		else: # Showing the add form
			form = AddArticleForm()
			form.validate_on_submit()

			if (doi is not None):
				import requests
				import json
				url = "http://dx.doi.org/"
				headers = {'Accept': 'application/vnd.citationstyles.csl+json;q=1.0'}
				if validate_doi(doi):
					form.doi_field.data = doi
					req = requests.get("{}{}".format(url,doi), headers=headers)
					if (req.status_code == requests.codes.ok): # Got a response
						# Now populate other field
						json_data = req.json()
						if (json_data[u'author']):
							authors_txt = u""
							for author in json_data[u'author']:
								if (author[u'family'] and author[u'given']):
									authors_txt += u"{last}, {firsts}\n".format(last=author[u'family'], firsts=author[u'given'])
							form.authors_field.data = authors_txt
						if (json_data[u'container-title']):
							form.journal_field.data = json_data[u'container-title']
						if (json_data[u'title']):
							form.title_field.data = json_data[u'title']
						if (json_data[u'volume']):
							form.volume_field.data = json_data[u'volume']					
						if (json_data[u'page']):
							form.pages_field.data = json_data[u'page']
						if (json_data[u'indexed']):
							indexed = json_data[u'indexed']
							if (indexed[u'date-parts']):
								form.year_field.data = indexed[u'date-parts'][0][0]
						


				return render_template('add.html', form=form)						
			else:
				#form = AddArticleForm()
				#form.validate_on_submit() # get error messages to the browser
				return render_template('add.html', form=form)				


	return app

if __name__ == '__main__':
	create_app(configfile="./config.py").run(debug=True)

