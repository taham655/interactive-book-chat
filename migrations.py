from flask_migrate import Migrate, upgrade
from app import app, db
from models import User, Book, Character, Conversation, Library, Favorite

migrate = Migrate(app, db)

def init_db():
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            print("Tables created successfully!")
        except Exception as e:
            print(f"Error creating tables: {e}")

if __name__ == '__main__':
    init_db()