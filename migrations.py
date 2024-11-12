# from app import app, db
# from flask_migrate import upgrade

# def init_db():
#     with app.app_context():
#         upgrade()

# if __name__ == '__main__':
#     init_db()

from flask import Flask
from flask_migrate import Migrate, upgrade
from app import app, db
from models import User, Library, Book, Character, Conversation, Favorite

migrate = Migrate(app, db)

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()