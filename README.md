doifetcher
==========

Website that fetches (specific) article information based on DOI.
Functionality is based on the web service at http://dx.doi.org/.

Website implementation uses the following components:
 * Python
 * Python-Flask - web microframework
 * Python-Response - creating custom http requests
 * Python-JSON - parsing the input from crosscite.org
 * MySQL (or sqlite3) - for storing the citations
 
