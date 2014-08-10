# -*- coding: utf-8 -*-

from doifetcher import create_app
app = create_app(".config.py")
app.run(debug=True)
