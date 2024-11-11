from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Book, Character, Conversation, Library, Favorite
from utils import process_pdf_content, extract_characters
from utils.ai_handler import generate_character_response
from werkzeug.utils import secure_filename
import os

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_book():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400

    filename = secure_filename(file.filename)
    content = process_pdf_content(file)
    
    book = Book(
        title=filename.replace('.pdf', ''),
        content=content,
        user_id=current_user.id
    )
    db.session.add(book)
    db.session.commit()
    
    characters = extract_characters(content)
    for char_name, char_desc in characters.items():
        character = Character(
            name=char_name,
            description=char_desc,
            book_id=book.id
        )
        db.session.add(character)
    db.session.commit()
    
    return jsonify({'success': True, 'book_id': book.id})

@app.route('/libraries', methods=['GET', 'POST'])
@login_required
def libraries():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Library name is required')
            return redirect(url_for('libraries'))
            
        library = Library(name=name, description=description, user_id=current_user.id)
        db.session.add(library)
        db.session.commit()
        flash('Library created successfully')
        
    libraries = current_user.libraries.all()
    return render_template('libraries.html', libraries=libraries)

@app.route('/library/<int:library_id>')
@login_required
def library_detail(library_id):
    library = Library.query.get_or_404(library_id)
    if library.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('libraries'))
    return render_template('library_detail.html', library=library)

@app.route('/library/<int:library_id>/add_book/<int:book_id>', methods=['POST'])
@login_required
def add_book_to_library(library_id, book_id):
    library = Library.query.get_or_404(library_id)
    book = Book.query.get_or_404(book_id)
    
    if library.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
        
    if book not in library.books:
        library.books.append(book)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Book already in library'}), 400

@app.route('/library/<int:library_id>/remove_book/<int:book_id>', methods=['POST'])
@login_required
def remove_book_from_library(library_id, book_id):
    library = Library.query.get_or_404(library_id)
    book = Book.query.get_or_404(book_id)
    
    if library.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
        
    if book in library.books:
        library.books.remove(book)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Book not in library'}), 400

@app.route('/favorites/toggle', methods=['POST'])
@login_required
def toggle_favorite():
    book_id = request.form.get('book_id')
    character_id = request.form.get('character_id')
    
    if not book_id and not character_id:
        return jsonify({'error': 'Either book_id or character_id is required'}), 400
        
    existing_favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        book_id=book_id,
        character_id=character_id
    ).first()
    
    if existing_favorite:
        db.session.delete(existing_favorite)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed'})
    
    favorite = Favorite(
        user_id=current_user.id,
        book_id=book_id,
        character_id=character_id
    )
    db.session.add(favorite)
    db.session.commit()
    return jsonify({'success': True, 'action': 'added'})

@app.route('/favorites')
@login_required
def favorites():
    favorite_books = Book.query.join(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.book_id.isnot(None)
    ).all()
    
    favorite_characters = Character.query.join(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.character_id.isnot(None)
    ).all()
    
    return render_template('favorites.html',
                         favorite_books=favorite_books,
                         favorite_characters=favorite_characters)

@app.route('/chat/<int:character_id>', methods=['GET', 'POST'])
@login_required
def chat(character_id):
    character = Character.query.get_or_404(character_id)
    if request.method == 'POST':
        message = request.form['message']
        
        # Save user message
        conversation = Conversation(
            user_id=current_user.id,
            character_id=character_id,
            message=message
        )
        db.session.add(conversation)
        db.session.commit()
        
        # Generate AI response using character context
        response = generate_character_response(
            character_name=character.name,
            character_description=character.description,
            book_content=character.book.content,
            user_message=message
        )
        
        # Save character response
        char_reply = Conversation(
            user_id=current_user.id,
            character_id=character_id,
            message=response,
            is_user=False
        )
        db.session.add(char_reply)
        db.session.commit()
        
        return jsonify({
            'message': response,
            'character_name': character.name
        })
    
    conversations = Conversation.query.filter_by(
        character_id=character_id,
        user_id=current_user.id
    ).order_by(Conversation.timestamp).all()
    
    return render_template('chat.html', 
                         character=character,
                         conversations=conversations)
