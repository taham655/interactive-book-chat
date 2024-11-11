from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    books = db.relationship('Book', backref='owner', lazy='dynamic')
    libraries = db.relationship('Library', backref='owner', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Library(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    books = db.relationship('Book', secondary='library_books', lazy='dynamic',
                          backref=db.backref('libraries', lazy='dynamic'))

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text)
    cover_path = db.Column(db.String(255))  # Path to the book cover image
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    characters = db.relationship('Character', backref='book', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='book', lazy='dynamic')

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    personality_traits = db.Column(db.JSON)
    emotional_profile = db.Column(db.JSON)
    relationships = db.Column(db.JSON)
    personality_summary = db.Column(db.Text)
    avatar_path = db.Column(db.String(255))  # Path to the character avatar image
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    conversations = db.relationship('Conversation', backref='character', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='character', lazy='dynamic')

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Association table for many-to-many relationship between libraries and books
library_books = db.Table('library_books',
    db.Column('library_id', db.Integer, db.ForeignKey('library.id'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True)
)
