import os
from flask import Flask
from extensions import db, login_manager

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "thefabled-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

# Initialize upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import routes after app creation to avoid circular imports
with app.app_context():
    from routes import *  # Import all routes
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
