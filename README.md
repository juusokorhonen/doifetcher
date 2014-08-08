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
 
Quick usage:
1. Install and learn how to use virtualenv and virtualenvwrapper
2. Install requirements: 
  $ pip install -r requirements.txt
2.1 Install citeproc-py from the source
3. Go to server/
4. run:
  $ python server.py
5. Use your browser to go to http://localhost:5000/
