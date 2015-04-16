# -*- coding: utf-8 -*-

import os

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "INSERT_SECRET_KEY_HERE"
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'test.db')
    SQLALCHEMY_MIGRATE_REPO = os.path.join(BASE_DIR, 'db_repository')
    OPENID_PROVIDERS = [
            {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
            {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'},
            {'name': 'LinkedIn', 'url': 'https://www.linkedin.com/uas/oauth2/authorization'}]
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
            'facebook': {
                'name': 'Facebook', 
                'id': 'INSERT_ID_HERE',
                'secret': 'INSERT_SECRET_HERE',
                'authorize_url': 'https://graph.facebook.com/oauth/authorize',
                'base_url': 'https://graph.facebook.com/',
                'access_token_url': 'https://graph.facebook.com/oauth_access_token',
                'always_use_defaults': False
                },
            'twitter': {
                'name': 'Twitter',
                'id': 'INSERT_ID_HERE',
                'secret': 'INSERT_SECRET_HERE',
                'request_token_url': 'https://api.twitter.com/oauth/request_token',
                'authorize_url': 'https://api.twitter.com/oauth/authorize',
                'base_url': 'https://api.twitter.com/1.1/',
                'access_token_url': 'https://api.twitter.com/oauth/access_token',
                'always_use_defaults': False
                }
            }

class DevelopmentConfig(Config):
    DEBUG = True 

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/doifetcher.db'

class ProductionConfig(Config):
    SECRET_KEY = "INSERT_SECRET_KEY_HERE"
    SQLALCHEMY_DATABASE_URI = 'mysql:////localhost'
