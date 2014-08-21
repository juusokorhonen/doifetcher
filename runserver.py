# -*- coding: utf-8 -*-

from doifetcher import create_app
from flask import url_for
from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig

app = create_app(config=DevelopmentConfig)
app.run()
