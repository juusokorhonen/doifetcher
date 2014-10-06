# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from nameparser import HumanName
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.orderinglist import ordering_list

db = SQLAlchemy() # db get bound to the app by using the init_app(app)-function

def populate_example_data(app, db):
    app.test_request_context().push()
    db.drop_all()
    db.create_all()
    db.session.commit()

class Author(db.Model):
    """Represents an author of an article. Each author can author many articles."""
    __tablename__ = 'authors'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(4096))
    first = db.Column(db.String(4096), nullable=False)
    middle = db.Column(db.String(4096))
    last = db.Column(db.String(4096), nullable=False)
    suffix = db.Column(db.String(4096))
    nickname = db.Column(db.String(4096))
    mod_date = db.Column(db.TIMESTAMP, nullable=False, default=db.func.now(), onupdate=db.func.now())

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

    def __repr__(self):
        #return '<Author %r>' % self.name()
        return u'{}'.format(self.name())
    
    def __unicode__(self):
        return self.__repr__()

class ArticleAuthor(db.Model):
    """Maps an ordered many-to-many relationship between articles and authors."""
    __tablename__ = 'article_authors'

    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), primary_key=True)
    author = db.relationship('Author')
    position = db.Column(db.Integer)

class Article(db.Model):
    """Represents an article, which can have many authors."""
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    doi = db.Column(db.String(4096))
    title = db.Column(db.String(4096))
    journal_id = db.Column(db.Integer, db.ForeignKey('journals.id'))
    journal = db.relationship('Journal',
            backref=db.backref('articles', lazy='dynamic'))
    volume = db.Column(db.String(4096))
    issue = db.Column(db.String(4096))
    pages = db.Column(db.String(4096))
    pub_date = db.Column(db.DateTime)
    add_date = db.Column(db.DateTime)
    json_data = db.Column(db.Text)
    _authors = db.relationship('ArticleAuthor',
            order_by='ArticleAuthor.position',
            collection_class=ordering_list('position'),
            cascade='all, delete-orphan',
            backref=db.backref('articles', lazy='joined'))
    authors = association_proxy('_authors', 'author',
            creator=lambda _a: ArticleAuthor(author=_a))
    mod_date = db.Column(db.TIMESTAMP, nullable=False, default=db.func.now(), onupdate=db.func.now())


    def __repr__(self):
        #return '<Article %r>' % self.doi
        return u'{}'.format(self.title)

    def __unicode__(self):
        return self.__repr__()

class Journal(db.Model):
    """Represents a (scientific) journal, which has a name and an optional abbreviation."""
    __tablename__ = "journals"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4096))
    abbreviation = db.Column(db.String(4096))
    mod_date = db.Column(db.TIMESTAMP, nullable=False, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        #return '<Journal %r>' % self.name
        return u'{}'.format(self.name)

    def __unicode__(self):
        return self.__repr__()
