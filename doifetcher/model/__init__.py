# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy() # db get bound to the app by using the init_app(app)-function

def populate_example_data(app, db):
    app.test_request_context().push()
    db.drop_all()
    db.create_all()

    js = []
    js.append(Journal(u'Nano Research', u'Nano Res.'))
    js.append(Journal(u'ChemSusChem'))
    js.append(Journal(u'Soft Matter'))
    js.append(Journal(u'Journal of Nanoparticle Research', 'J. Nanopart. Res.'))
    arts = []
    arts.append(Article(u'10.1007/s12274-012-0282-6',
                     u'Single-walled carbon nanotube networks for ethanol vapor sensing applications',
                     js[0],
                     datetime(2013,02,01)))
    arts.append(Article(u'10.1039/C2SM26932E',
                              u'The role of hemicellulose in nanofibrillated cellulose networks',
                              js[2],
                              datetime(2012,11,20)))
    arts.append(Article(u'10.1007/s11051-013-1883-z',
                                    u'High gradient magnetic separation of upconverting lanthanide nanophosphors based on their intrinsic paramagnetism',
                                    js[3],
                                    datetime(2013,8,1)))
    arts.append(Article(u'10.1007/s11051-013-1850-8',
                             u'Enhancement of blue upconversion luminescence in hexagonal NaYF4:Yb,Tm by using K and Sc ions',
                             js[0],
                             datetime(2013,7,1)))
    
    for j in js:
        db.session.add(j)
    for a in arts:
        db.session.add(a)
    db.session.commit()


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doi = db.Column(db.String(1024), unique=True)
    title = db.Column(db.String(4096))
    journal_id = db.Column(db.Integer, db.ForeignKey('journal.id'))
    journal = db.relationship('Journal',
            backref=db.backref('articles', lazy='dynamic'))
    pub_date = db.Column(db.DateTime)
    add_date = db.Column(db.DateTime)

    def __init__(self, doi, title, journal, pub_date, add_date=None):
        self.doi = doi
        self.title = title
        self.journal = journal
        self.pub_date = pub_date
        if (add_date is None):
            add_date = datetime.utcnow()
        self.add_date = add_date
        self.journal = journal

    def __repr__(self):
        return '<Article %r>' % self.doi

class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4096))
    abbreviation = db.Column(db.String(4096))

    def __init__(self, name, abbreviation=None):
        self.name = name
        if (abbreviation is None):
            abbreviation = name
        self.abbreviation = abbreviation

    def __repr__(self):
        return '<Journal %r>' % self.name
