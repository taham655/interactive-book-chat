from app import app, db
from flask_migrate import upgrade

def init_db():
    with app.app_context():
        upgrade()

if __name__ == '__main__':
    init_db()
