from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Book, Character, Conversation
from utils import process_pdf_content, extract_characters
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

@app.route('/chat/<int:character_id>', methods=['GET', 'POST'])
@login_required
def chat(character_id):
    character = Character.query.get_or_404(character_id)
    if request.method == 'POST':
        message = request.form['message']
        conversation = Conversation(
            user_id=current_user.id,
            character_id=character_id,
            message=message
        )
        db.session.add(conversation)
        db.session.commit()
        
        # Generate character response (simplified for now)
        response = f"As {character.name}, I acknowledge your message: {message}"
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
