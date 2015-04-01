# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

import re
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from nameparser import HumanName
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.orderinglist import ordering_list

db = SQLAlchemy() # db get bound to the app by using the init_app(app)-function

def db_type():
    """
    Returns the database type we are using. It's based on config variable.
    """
    from config import Config
    m = re.search('^(\w+)', Config.SQLALCHEMY_DATABASE_URI)
    return m.group(0)

class User(db.Model):
    """
    A user is for logging into the system. A user can map to several authors.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(256), index=True, unique=True)
    nickname = db.Column(db.String(128), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    name = db.Column(db.String(1024))
    admin = db.Column(db.Boolean, default=False)

    def is_authenticated(self):
        """
        This method should return true unless the user is not allowed to be authenticated.
        """
        return True

    def is_active(self):
        """
        This method should return true unless the user is inactive for some reason (banned?).
        """
        return True

    def is_anonymous(self):
        """
        This method should return true only for fake users that are not supposed to log into the system.
        """
        return False

    def get_id(self):
        """
        This method should return a unique id for a user in unicode format.
        """
        try:
            return unicode(self.id)
        except NameError:
            return str(self.id) # python 3

    def is_admin(self):
        """
        This method returns true if user is admin and should have more privileges.
        """
        return self.admin

    def __repr__(self):
        return "<User %r>" % (self.nickname)
    
    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

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
    if (db_type() == 'sqlite'):
        mod_date = db.Column(db.TIMESTAMP, nullable=False)
    else:
        mod_date = db.Column(db.TIMESTAMP, nullable=False, default=db.func.now(), onupdate=db.func.now())
    inserter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    inserter = db.relationship('User', backref=db.backref('articles', lazy='dynamic'))

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


