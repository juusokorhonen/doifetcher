# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from nameparser import HumanName

db = SQLAlchemy() # db get bound to the app by using the init_app(app)-function

def populate_example_data(app, db):
    app.test_request_context().push()
    db.drop_all()
    db.create_all()

    js = []
    js.append(Journal(name=u'Nano Research', abbreviation=u'Nano Res.'))
    js.append(Journal(name=u'ChemSusChem'))
    js.append(Journal(name=u'Soft Matter'))
    js.append(Journal(name=u'Journal of Nanoparticle Research', abbreviation='J. Nanopart. Res.'))
    arts = []
    arts.append(Article(doi=u'10.1007/s12274-012-0282-6',
                     title=u'Single-walled carbon nanotube networks for ethanol vapor sensing applications',
                     journal=js[0],
                     pub_date=datetime(2013,02,01)))
    arts.append(Article(doi=u'10.1039/C2SM26932E',
                              title=u'The role of hemicellulose in nanofibrillated cellulose networks',
                              journal=js[2],
                              pub_date=datetime(2012,11,20)))
    arts.append(Article(doi=u'10.1007/s11051-013-1883-z',
                                    title=u'High gradient magnetic separation of upconverting lanthanide nanophosphors based on their intrinsic paramagnetism',
                                    journal=js[3],
                                    pub_date=datetime(2013,8,1)))
    arts.append(Article(doi=u'10.1007/s11051-013-1850-8',
                             title=u'Enhancement of blue upconversion luminescence in hexagonal NaYF4:Yb,Tm by using K and Sc ions',
                             journal=js[0],
                             pub_date=datetime(2013,7,1)))
    
    for j in js:
        db.session.add(j)
    for a in arts:
        db.session.add(a)
    db.session.commit()

# Helper table for many-to-many relationships
article_to_author = db.Table('article_to_author',
        db.Column('article_id', db.Integer, db.ForeignKey('article.id')),
        db.Column('author_id', db.Integer, db.ForeignKey('author.id')))

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doi = db.Column(db.String(4096))
    title = db.Column(db.String(4096))
    journal_id = db.Column(db.Integer, db.ForeignKey('journal.id'))
    journal = db.relationship('Journal',
            backref=db.backref('articles', lazy='dynamic'))
    volume = db.Column(db.String(4096))
    pages = db.Column(db.String(4096))
    pub_date = db.Column(db.DateTime)
    add_date = db.Column(db.DateTime)
    mod_date = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.current_timestamp())
    json_data = db.Column(db.Text)
    authors = db.relationship('Author', secondary=article_to_author,
            backref=db.backref('articles', lazy='dynamic'))

    def __repr__(self):
        return '<Article %r>' % self.doi

class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4096), unique=True)
    abbreviation = db.Column(db.String(4096))

    def __repr__(self):
        return '<Journal %r>' % self.name

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(4096))
    first = db.Column(db.String(4096), nullable=False)
    middle = db.Column(db.String(4096))
    last = db.Column(db.String(4096), nullable=False)
    suffix = db.Column(db.String(4096))
    nickname = db.Column(db.String(4096))

    def __repr__(self):
        return u"<Author {}, {} {}>".format(self.last, self.first, self.middle)

    def __eq__(self, other):
        """
        Checks for the equality of two authors. Basically sees if both first and last names match.
        If both have middle names, then also matches those. Otherwise ignores them.
        """
        if (isinstance(other, Author)):
            if (self.first.lower() == other.first.lower() and self.last.lower() == other.last.lower()):
                if (self.middle is not None and self.middle is not None):
                    return (self.middle.lower() == other.middle.lower())
                return True
        return NotImplemented

    def __ne__(self, other):
        """
        Check the inequality of two Author objects.
        """
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal

    def name(self):
        if (self.middle):
            return u"{}, {} {}".format(self.last, self.first, self.middle)
        return u"{}, {}".format(self.last, self.first)
