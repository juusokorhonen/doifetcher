# -*- coding: utf-8 -*-

import os

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "INSERT_SECRET_KEY_HERE"
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'test.db')
    SQLALCHEMY_MIGRATE_REPO = os.path.join(BASE_DIR, 'db_repository')
    OAUTH_CREDENTIALS = {
            'google': {
                'name': 'Google', 
                'id': 'INSERT_CLIENT_ID_FROM_https://console.developers.google.com/',
                'secret': 'INSERT_CLIENT_SECRET_FROM_https://console.developers.google.com',
                'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
                'base_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
                'access_token_url': 'https://www.googleapis.com/oauth2/v3/token',
                'configuration_url': 'https://accounts.google.com/.well-known/openid-configuration',
                'always_use_defaults': False
                },
            }

class DevelopmentConfig(Config):
    DEBUG = True 
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'testing.db')

class ProductionConfig(Config):
    SECRET_KEY = "INSERT_PRODUCTION_SECRET_KEY_HERE"
    SQLALCHEMY_DATABASE_URI = 'mysql:////localhost'
