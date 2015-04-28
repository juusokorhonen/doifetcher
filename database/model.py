# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

import re
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
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

class User(UserMixin, db.Model):
    """
    A user is for logging into the system. A user can map to several authors.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), unique=True, nullable=False)
    nickname = db.Column(db.String(128))
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

    def __unicode__(self):
        if (self.name is not None and self.name != ''):
            return "{} ({})".format(self.name, self.email)
        return self.email

    def __repr__(self):
        return "<User %r>" % (self.email)
   
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

class OAuthUser(db.Model):
    """
    Represents a mapping of User to a OAuth provider.
    """
    __tablename__ = 'oauthusers'
    id = db.Column(db.Integer, primary_key=True)
    oauth_id = db.Column(db.String(257), nullable=False)
    provider = db.Column(db.String(128), nullable=False)
    user_id  = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('oauths', lazy='dynamic'))
    __table_args__ = (db.UniqueConstraint('provider', 'oauth_id', name='_unique_oauth_id'),)

    def __unicode__(self):
        return "{} @ {}".format(self.oauth_id, self.provider)

    def __repr__(self):
        return "<OAuthUser %r @ %r>" % (self.oauth_id, self.provider)

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
    if (db_type() == 'sqlite'):
        mod_date = db.Column(db.TIMESTAMP, nullable=False)
    else:
        mod_date = db.Column(db.TIMESTAMP, nullable=False, default=db.func.now(), onupdate=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('authors', lazy='dynamic'))

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

    article_id = db.Column(db.Integer, db.ForeignKey('articles.id', onupdate='CASCADE'), primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id', onupdate='CASCADE'), primary_key=True)
    position = db.Column(db.Integer, nullable=False)
    article = db.relationship('Article', backref=db.backref('author_assoc', cascade='all,delete-orphan', single_parent=True))
    author = db.relationship('Author', backref=db.backref('article_assoc', cascade='all,delete-orphan', single_parent=True))

    def __unicode__(self):
        return "({}) {}".format(self.position, self.author.name())

class ArticleTag(db.Model):
    """Maps an article to a tag."""
    __tablename__ = 'article_tags'

    article_id = db.Column(db.Integer, db.ForeignKey('articles.id', onupdate='CASCADE'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id', onupdate='CASCADE'), primary_key=True)
    #article = db.relationship('Article', backref=db.backref('tag_assoc'))
    #tag = db.relationship('Tag', backref=db.backref('article_assoc'))

    def __unicode__(self):
        return "{}".format(self.tag.name)

class Article(db.Model):
    """Represents an article, which can have many authors."""
    __tablename__ = 'articles'

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
    authors = db.relationship("Author", secondary='article_authors', passive_updates=False, order_by='ArticleAuthor.position',
            backref=db.backref('articles', cascade='all,delete-orphan', single_parent=True))
    tags = db.relationship('Tag', secondary='article_tags', backref=db.backref('articles', lazy='dynamic'))

    if (db_type() == 'sqlite'):
        mod_date = db.Column(db.TIMESTAMP, nullable=False)
    else:
        mod_date = db.Column(db.TIMESTAMP, nullable=False, default=db.func.now(), onupdate=db.func.now())
    inserter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    inserter = db.relationship('User', backref=db.backref('added_articles', lazy='dynamic'))
    inserter_ip = db.Column(db.String(128))

    def __repr__(self):
        #return '<Article %r>' % self.doi
        return u'{}'.format(self.title)

    def citation(self, authors=True):
        citation_text = ''
       
        if authors:
            num_authors = len(self.authors)
            cnt = 0
            for author in self.authors:
                if author.middle is not None:
                    citation_text += "{first} {middle} {last}".format(first=author.first, middle=author.middle, last=author.last)
                else:
                    citation_text += "{first} {last}".format(first=author.first, last=author.last)
                cnt += 1
                if cnt < num_authors:
                    citation_text += ", "
                else:
                    citation_text += ". "
        
        if self.title is not None:
            citation_text += "{}, ".format(self.title)
        
        if self.journal.abbreviation is not None:
            citation_text += "{} ".format(self.journal.abbreviation)
        elif self.journal is not None:
            citation_text += "{} ".format(self.journal.name)

        if self.pub_date.year is not None:
            citation_text += "({}) ".format(self.pub_date.year)

        if self.volume is not None:
            citation_text += "{}".format(self.volume)

        if self.pages is not None:
            citation_text += ", {}.".format(self.pages)
        else:
            citation_text += "."

        if self.doi is not None:
            citation_text += " DOI: {}.".format(self.doi)

        return citation_text

    def __unicode__(self):
        return self.citation(authors=False)

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

class Tag(db.Model):
    """Represents a tag on an article. A tag can be anything."""
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)

    def __unicode__(self):
        return "{}".format(self.name)
