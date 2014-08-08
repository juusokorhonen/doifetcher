#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import requests 
from citeproc.py2compat import *
import json

dois = ["10.1126/science.169.3946.635", "10.1007/s12274-012-0282-6", "10.1016/j.susc.2013.06.005"]
url = "http://dx.doi.org/"
headers = {'Accept': 'application/vnd.citationstyles.csl+json;q=1.0'}

reqs = []
for doi in dois:
		tempr = requests.get("{}/{}".format(url,doi), headers=headers)

		print("---")
		print("  URL: {}".format(tempr.url))
		print("  Response code: {}".format(tempr.status_code))
		print("  Request ok: {}".format(tempr.status_code == requests.codes.ok))
		print("  Headers: {}".format(tempr.headers))
		print("  Text: {}".format(tempr.text))
		print("  JSON: {}".format(tempr.json()))
		print("\n\n")
		if (tempr.status_code == requests.codes.ok):
			reqs.append(tempr)

print("Moving on to parse the JSON...\n\n")

# Import the citeproc-py classes we'll use below.
from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import Citation, CitationItem
from citeproc import formatter
from citeproc.source.json import CiteProcJSON

# We'll assume that requests generates a proper JSON object
#json_data = json.loads(r.text)
counter = 0
json_data = []
for r in reqs:
	tempjson = r.json()
	tempjson.update({u'id': u"{}".format(tempjson[u'DOI'])})
	counter += 1
	json_data.append(tempjson)

print("json_data: {}".format(json_data))

# Process the JSON data to generate a citeproc-py BibliographySource
bib_source = CiteProcJSON(json_data)

# DEBUG:
for key,entry in bib_source.items():
	print(key)
	for name,value in entry.items():
		print('    {}: {}'.format(name, value))

print("\n\nEntries read into parser.\n\n")

# Load a CSL style (from a source current directory)
bib_style = CitationStylesStyle('nature')

# Create the citeproc-py biboliography, by passing it the:
# * CitationStylesStyle
# * BibliographySource (CiteProcJSON in this case), and
# * a formatter (plain, html, or a custom one)
bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.plain)

def warn(citation_item):
	print("WARNING: Reference with key '{}' not found in the bibliography.".format(citation_item.key))

print("\n\nBibliography")
print("---------")

for item in bibliography.bibliography():
	print(str(item))
