# -*- coding: utf-8 -*-

from doifetcher import create_app
from flask import url_for
app = create_app("config.py")
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        print("{} : {} : {}".format(rule.rule, rule.endpoint, app.view_functions[rule.endpoint]))
app.run()
