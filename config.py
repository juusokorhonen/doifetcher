# -*- coding: utf-8 -*-

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "df2x1aqw%6&y8k4@!u-hj8e8*5&)58_t(@9wyc%*+847p90uxnh2ewf3"

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/doifetcher.db'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/doifetcher.db'

class ProductionConfig(Config):
    SECRET_KEY = "@9Wyc%*+847p90uXnh2ewf3Df2x1aqw%6&y8k4@!u-hJ8e8*5&)58_t("
    SQLALCHEMY_DATABASE_URI = 'mysql:////localhost'
