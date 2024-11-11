from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Book, Character, Conversation, Library, Favorite
from utils import process_pdf_content, extract_characters
from utils.ai_handler import generate_character_response
from utils.recommendations import get_recommendations
from utils.image_optimizer import optimize_image, get_image_dimensions
from utils.template_helpers import responsive_image
from werkzeug.utils import secure_filename
import os

# Add to your existing imports and configurations
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@app.route('/')
def index():
    if current_user.is_authenticated:
        recommended_books = get_recommendations(current_user)
        return render_template('index.html', recommended_books=recommended_books)
    return render_template('index.html', recommended_books=[])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        user = User.query.filter_by(email=request.form['email']).first()
        if user:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=request.form['username'], email=request.form['email'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page if next_page else url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/test_image_upload')
@login_required
def test_image_upload():
    return render_template('image_test.html')

@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
        
    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not allowed_image_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({'error': 'Invalid filename'}), 400

        upload_folder = os.path.join(app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Generate optimized versions
        name, ext = os.path.splitext(filename)
        output_base = os.path.join(upload_folder, name)
        
        optimized_images = optimize_image(file_path, output_base)
        # Remove original upload after optimization
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Convert paths to URLs
        for img in optimized_images:
            img['path'] = img['path'].replace(app.static_folder, '/static')
            
        return jsonify({
            'success': True,
            'images': optimized_images,
            'base_path': f'/static/uploads/{name}'
        })
    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500

# Add responsive_image to template context
@app.context_processor
def utility_processor():
    return dict(responsive_image=responsive_image)
