doifetcher
==========

Website that fetches (specific) article information based on DOI.
Functionality is based on the web service at http://dx.doi.org/.

Website implementation uses the following components:
 * Python (Python license, GPL compatible)
 * Python-Flask - web microframework (Flask license, three clause BSD license)
 * Flask-AppConfig - Easy configuring library for Flask (MIT license)
 * Flask-Bootstrap - Twitter Bootstrap library for Flask (BSD license)
 * WTForms - Easy forms in web pages (BSD license)
 * Flask-WTF - WTForms library for Flask (BSD license)
 * Requests - Customizable HTTP requests for Python (Apache 2.0 license)
 * [ lxml - XML and HTML processing in Python (BSD license, libxml2 and libxslt2 under MIT license)]
 * SQLAlchemy - Object Relational Mapper for database connectivity (MIT license) 
 * Flask-SQLAlchemy - SQLAlchemy library for Flask (BSD license)
 * Python-JSON - parsing the input from crosscite.org (LGPL license)
 * MySQL (or sqlite3) - for storing the citations (various licensing schemes, see http://www.mysql.com/about/legal/licensing/)
 * Python-Nameparser - For parsing names into firstname, middlename and lastname (LGPL license)
 * [ Bibtexparser - For abbreviating journal names (LGPLv3 license) ]
 * [ Charder - For character encoding detection (LGPL license) ]
A very import aspect of the program is provided by the REST API at http://dx.doi.org. See http://www.doi.org/factsheets/DOIProxy.html#rest-api

[ The ones shown in brackets were used at some point, but are not currently required. ]

Deployment
----------

Deployment example (probably does not work for you out-of-the-box):
0.	Download and unpack the release archive
1.	Install python2.7
	$ sudo apt-get instal python2.7 (Debian Linux)
2.	Install pip
	$ sudo easy_install pip
3.	Install virtualenv
	$ sudo pip install virtualenv
4.	Go to the software base folder (this folder)
5.	Set up virtualenv
	$ virtualenv venv
6.	Activate vitualenv
	$ . venv/bin/activate
7.	Make sure that your system has required libraries installed
	$ sudo apt-get install libxml2-dev libxslt-dev
	$ sudo apt-get install libmysqlclient-dev
8.	Install python requirements
	$ pip install -r requirements.txt
9.	Create database
	$ mysql -u root -p
	$$ CREATE DATABASE doifetcherdb
	$$ GRANT ALL PRIVILEGES ON doifetcherdb.* TO 'username' IDENTIFIED BY 'password'
	$$ FLUSH PRIVILEGES
10.	Update config.py
	class TestingConfig:
		TESTING = True
		SECRET_KEY = '(Generate secret key here, eg. http://www.miniwebtool.com/django-secret-key-generator/)'
		SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/doifetcherdb'
11.	Update doifetcher.wsgi
	# -*- coding: utf-8 -*-
	activate_venv = '/path/to/install/dir/venv/bin/activate_this.py'
	execfile(activate_venv, dict(__file__=activate_venv))
	import sys
	sys.path.insert(0, '/path/to/install/dir')
	from doifetcher import create_app
	from config import Config, TestingConfig
	application = create_app(config=TestingConfig)
12.	Set up apache-wsgi (http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/)
	$ sudo apt-get install libapache2-mod-wsgi
12.1	Configure apache (read the apache docs or find a tutorial, if you don't know how)
	<VirtualHost *>
		ServerName yourdomainname.com
		WSGIDaemonProcess doifetcher_process user=user1 group=group1 threads=5
		WSGIScriptAlias /doifetcher /path/to/install/dir/doifetcher.wsgi
		WSGIScriptRelading On
		<Directory /path/to/install/dir>
			WSGIProcessGroup doifetcher_process
			WSGIApplicationGroup %{GLOBAL}
			Order deny,allow
			Allow from all
		</Directory>
	</VirtualHost>
12.2	Test config
	$ sudo apache2ctl configtest
	$ sudo apache2ctl restart
13.	You should now be able to browse to http://yourdomainname.com/doifetcher/ and see the front page
14.	Set up database tables
	$ python
	$$ from doifetcher import create_app
	$$ from config import TestingConfig
	$$ app = create_app(config=TestingConfig)
	$$ app.test_request_context().push()
	$$ from doifetcher.model import db
	$$ db.init_app(app)
	$$ db.create_all()
15.	Database connectivity should now be set up assuming that you did not run into problems on the way.
