# -*- coding: utf-8 -*-

import os

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "b3ny=xchgt6h^z)#lorsuspll5p47ng(7_upmb*#qkcl=s)14s"
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'test.db')
    SQLALCHEMY_MIGRATE_REPO = os.path.join(BASE_DIR, 'db_repository')
    OAUTH_CREDENTIALS = {
            'google': {
                'name': 'Google', 
                'id': 'INSERT_ID_HERE',
                'secret': 'INSERT_SECRET_HERE',
                'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
                'base_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
                'access_token_url': 'https://www.googleapis.com/oauth2/v3/token',
                'always_use_defaults': False
                },
               }

class DevelopmentConfig(Config):
    DEBUG = True 

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/doifetcher.db'

class ProductionConfig(Config):
    SECRET_KEY = "INSERT_SECRET_KEY_HERE"
    SQLALCHEMY_DATABASE_URI = 'mysql:////localhost'
