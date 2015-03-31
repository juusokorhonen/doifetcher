# -*- coding: utf-8 -*-

import os

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "df2x1aqw%6&y8k4@!u-hj8e8*5&)58_t(@9wyc%*+847p90uxnh2ewf3"
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'test.db')
    SQLALCHEMY_MIGRATE_REPO = os.path.join(BASE_DIR, 'db_repository')
    OPENID_PROVIDERS = [
            {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
            {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'},
            {'name': 'LinkedIn', 'url': 'https://www.linkedin.com/uas/oauth2/authorization'}]


class DevelopmentConfig(Config):
    DEBUG = True 

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/doifetcher.db'

class ProductionConfig(Config):
    SECRET_KEY = "@9Wyc%*+847p90uXnh2ewf3Df2x1aqw%6&y8k4@!u-hJ8e8*5&)58_t("
    SQLALCHEMY_DATABASE_URI = 'mysql:////localhost'
