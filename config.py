# -*- coding: utf-8 -*-

import os

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "df2x1aqw%6&y8k4@!u-hj8e8*5&)58_t(@9wyc%*+847p90uxnh2ewf3"
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'test.db')
    SQLALCHEMY_MIGRATE_REPO = os.path.join(BASE_DIR, 'db_repository')
    OAUTH_CREDENTIALS = {
            'google': {
                'name': 'Google', 
                'id': '1051499551182-vn5ohho1aljagspulv5c440h1hu8idpm.apps.googleusercontent.com',
                'secret': 's9QYCbLK80gq1Jx9l33AHhO5',
                'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
                'base_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
                'access_token_url': 'https://www.googleapis.com/oauth2/v3/token',
                'configuration_url': 'https://accounts.google.com/.well-known/openid-configuration',
                'always_use_defaults': False
                },
            }

class DevelopmentConfig(Config):
    DEBUG = True 

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/doifetcher.db'

class ProductionConfig(Config):
    SECRET_KEY = "@9Wyc%*+847p90uXnh2ewf3Df2x1aqw%6&y8k4@!u-hJ8e8*5&)58_t("
    SQLALCHEMY_DATABASE_URI = 'mysql:////localhost'
