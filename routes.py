from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Book, Character, Conversation, Library, Favorite
from utils import (
    process_pdf_content,
    extract_text_from_epub,
    extract_characters,
    generate_character_response,
    analyze_book,
    create_character_prompt,
    initialize_chat_model,
    initialize_chat,
    get_chatbot_response
)
from utils.recommendations import get_recommendations
from utils.image_helpers import generate_responsive_images, get_image_dimensions
from werkzeug.utils import secure_filename
import os
import json
import asyncio

# Add new constant for image upload directory
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
os.makedirs(os.path.join(UPLOAD_FOLDER, 'books'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'characters'), exist_ok=True)

def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@app.route('/')
def index():
    recommended_books = []
    if current_user.is_authenticated:
        recommended_books = get_recommendations(current_user)
    return render_template('index.html', recommended_books=recommended_books)

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

@app.route('/upload-section')
@login_required
def upload_section():
    """Upload section page"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
@login_required
def upload_book():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        cover_image = request.files.get('cover_image')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are supported'}), 400

        # Save the file first
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Process the saved file
        try:
            content = process_pdf_content(file_path)
        except Exception as e:
            os.remove(file_path)  # Clean up the file if processing fails
            return jsonify({'error': f'Failed to process PDF: {str(e)}'}), 500

        # Handle cover image
        cover_path = None
        if cover_image and allowed_image_file(cover_image.filename):
            try:
                image_filename = secure_filename(cover_image.filename)
                base_path = os.path.join('uploads', 'books', os.path.splitext(image_filename)[0])
                cover_image_path = os.path.join(UPLOAD_FOLDER, 'books', image_filename)
                cover_image.save(cover_image_path)
                generate_responsive_images(cover_image_path, os.path.join(UPLOAD_FOLDER, 'books'))
                cover_path = base_path
            except Exception as e:
                return jsonify({'error': f'Failed to process cover image: {str(e)}'}), 500

        # Create book record
        book = Book(
            title=filename.replace('.pdf', ''),
            content=content,
            user_id=current_user.id,
            cover_path=cover_path
        )
        db.session.add(book)
        db.session.commit()

        # Process characters
        try:
            characters = asyncio.run(extract_characters(content))
            for char_name, char_data in characters.items():
                character = Character(
                    name=char_name,
                    description=char_data["description"],
                    personality_traits=char_data["personality_traits"],
                    emotional_profile=char_data["emotional_profile"],
                    relationships=char_data["relationships"],
                    personality_summary=char_data["personality_summary"],
                    book_id=book.id
                )
                db.session.add(character)
            db.session.commit()
        except Exception as e:
            return jsonify({'error': f'Failed to process characters: {str(e)}'}), 500

        return jsonify({'success': True, 'book_id': book.id})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

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

@app.route('/book/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if book.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
        
    try:
        # Get all character IDs for this book first
        character_ids = [char.id for char in Character.query.filter_by(book_id=book_id).all()]
        
        # Delete conversations for all characters
        for char_id in character_ids:
            Conversation.query.filter_by(character_id=char_id).delete(synchronize_session='fetch')
            
        # Delete favorites
        Favorite.query.filter_by(book_id=book_id).delete(synchronize_session='fetch')
        
        # Delete characters
        Character.query.filter_by(book_id=book_id).delete(synchronize_session='fetch')
        
        # Remove book from libraries
        book.libraries = []
        
        # Delete the book
        db.session.delete(book)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/chat/<int:character_id>', methods=['GET', 'POST'])
@login_required
def chat(character_id):
    character = Character.query.get_or_404(character_id)
    
    if request.method == 'POST':
        message = request.form['message']
        
        # Get existing conversation history
        conversations = Conversation.query.filter_by(
            character_id=character_id,
            user_id=current_user.id
        ).order_by(Conversation.timestamp).all()
        
        # Format conversation history for the AI
        messages = [
            {
                "role": "assistant" if not conv.is_user else "user",
                "content": conv.message
            }
            for conv in conversations
        ]
        
        # Create character prompt with safe fallbacks
        character_details = {
            'basic_info': {
                'name': character.name,
                'role': getattr(character, 'role', 'Unknown'),  # Fallback if role is missing
                'plot_importance': character.personality_summary or '',
                'key_relationships': character.relationships or []
            },
            'description': {
                'detailed_description': character.description or '',
                'llm_persona_prompt': getattr(character, 'llm_persona_prompt', '')
            },
            'depth': {
                'character_arc': character.emotional_profile.get('character_arc', '') if character.emotional_profile else '',
                'personality_traits': character.personality_traits or [],
                'memorable_quotes': character.emotional_profile.get('memorable_quotes', []) if character.emotional_profile else []
            }
        }
        
        character_prompt = create_character_prompt(character_details)
        
        # Generate AI response using new system
        response = generate_character_response(
            character_prompt=character_prompt,
            messages=messages,
            user_message=message,
            model=initialize_chat_model()
        )
        
        # Save user message
        user_message = Conversation(
            user_id=current_user.id,
            character_id=character_id,
            message=message,
            is_user=True
        )
        db.session.add(user_message)
        
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
    
    # GET request - show chat interface
    conversations = Conversation.query.filter_by(
        character_id=character_id,
        user_id=current_user.id
    ).order_by(Conversation.timestamp).all()
    
    return render_template('chat.html', 
                         character=character,
                         conversations=conversations)

@app.route('/chat/initialize', methods=['POST'])
@login_required
def initialize_character_chat():
    """Initialize or reset chat with a new character"""
    selected_character = request.json.get('character')
    if not selected_character:
        return jsonify({'error': 'No character selected'}), 400
    
    try:
        # Load character analysis data
        with open('character_analysis.json', 'r', encoding='utf-8') as f:
            character_data = json.load(f)
        
        # Initialize chat with selected character
        character_prompt, character_name = initialize_chat(selected_character, character_data)
        
        # Store in session
        session['character_prompt'] = character_prompt
        session['current_character'] = character_name
        session['messages'] = []
        
        return jsonify({
            'success': True,
            'character_name': character_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/message', methods=['POST'])
@login_required
def chat_message():
    """Handle individual chat messages"""
    if 'current_character' not in session:
        return jsonify({'error': 'No active character chat'}), 400
    
    message = request.json.get('message')
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Get response using the character's prompt
        model = initialize_chat_model()
        response = get_chatbot_response(
            prompt=session['character_prompt'],
            messages=session['messages'],
            model=model
        )
        
        if response:
            # Update session messages
            session['messages'].append({"role": "user", "content": message})
            session['messages'].append({"role": "assistant", "content": response})
            
            return jsonify({'response': response})
        else:
            return jsonify({'error': 'Failed to get response'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500