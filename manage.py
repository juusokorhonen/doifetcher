# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals, print_function, division)

import os
from flask.ext.script import Manager, Server

from server import create_app
from flask import url_for
from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig

app = create_app(config=TestingConfig)
manager = Manager(app)

manager.add_command("runserver", Server(
    use_debugger = app.config.get('DEBUG', True),
    use_reloader = app.config.get('DEBUG', True),
    host = app.config.get('HOST', '0.0.0.0'))
    )

@manager.command
def init_db():
    from migrate.versioning import api
    from database.model import db
    
    print("Initializing database (going to drop all tables)...")
    #app.test_request_context().push()
    db.drop_all()
    db.create_all()
    
    print("Versioning the database...")
    if not os.path.exists(app.config.get('SQLALCHEMY_MIGRATE_REPO')):
        api.create(app.config.get('SQLALCHEMY_MIGRATE_REPO'), 'database repository')
        api.version_control(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'))
    else:
        api.version_control(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'), api.version(app.config.get('SQLALCHEMY_MIGRATE_REPO')))
    db.session.commit()
    
    print("All done.")

@manager.command
def migrate_db():
    import imp
    from migrate.versioning import api
    from database.model import db
    
    print("Migrating the database...")
    v = api.db_version(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'))
    migration = app.config.get('SQLALCHEMY_MIGRATE_REPO') + ('/versions/%03d_migration.py' % (v+1))

    tmp_module = imp.new_module('old_model')
    old_model = api.create_model(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'))
    exec(old_model, tmp_module.__dict__)

    script = api.make_update_script_for_model(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'), tmp_module.meta, db.metadata)
    open(migration, "wt").write(script)

    api.upgrade(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'))
    v = api.db_version(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'))
    print("New migration saved as " + migration)
    print("Current database version: " + str(v))

@manager.command
def upgrade_db():
    from migrate.versioning import api
    
    api.upgrade(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'))
    v = api.db_version(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'))
    print('Current database version: ' + str(v))

@manager.command
def downgrade_db():
    from migrate.versioning import api

    v = api.db_version(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'))
    api.downgrade(app.config.get('SQLALCHEMY_DATABASE_URI'), app.config.get('SQLALCHEMY_MIGRATE_REPO'), v-1)
    print('Current database version: ' + str(v))




if __name__ == '__main__':
    manager.run()
