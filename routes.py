from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from app import app, db
from models import User, Book, Character, Conversation, Library, Favorite
from utils import (
    process_pdf_content,
    extract_text_from_epub,
    extract_characters,
    analyze_book_metadata_sync,
    ingest_book,  # Imported ingest_book
    generate_character_response,
    analyze_book,
    create_character_prompt,
    initialize_chat_model,
    initialize_chat,
    get_chatbot_response
    )

from werkzeug.utils import secure_filename
import os
import json
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add new constant for image upload directory
UPLOAD_FOLDER = os.path.join('static', 'uploads')

# Ensure upload directory exists
os.makedirs(os.path.join(UPLOAD_FOLDER, 'books'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'characters'), exist_ok=True)

# Configure app upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def anonymous_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return redirect(url_for('landing'))

@app.route('/landing')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('landing.html')

@app.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    books_pagination = Book.query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('index.html',
        total_books=Book.query.count(),
        total_characters=Character.query.count(),
        total_conversations=Conversation.query.count(),
        books=books_pagination.items,
        pagination=books_pagination
    )

@app.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        logger.info(f"Login attempt for username: {username}")  # Logging

        user = User.query.filter_by(username=username).first()
        logger.info(f"User query result: {user is not None}")  # Logging

        if user and user.check_password(password):
            logger.info("Password verified successfully")  # Logging
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))

        logger.warning("Login failed")  # Logging
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    session.pop('character_prompt', None)
    session.pop('current_character', None)
    session.pop('messages', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('landing'))

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

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not (file.filename.endswith('.pdf') or file.filename.endswith('.epub')):
            return jsonify({'error': 'Only PDF and EPUB files are supported'}), 400

        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        os.chmod(file_path, 0o600)

        # Determine file type and process content
        file_type = 'pdf' if filename.lower().endswith('.pdf') else 'epub'
        content = process_pdf_content(open(file_path, 'rb')) if file_type == 'pdf' else extract_text_from_epub(file_path)
        metadata = analyze_book_metadata_sync(content[:15000])

        # Create book record
        book = Book(
            title=metadata.get('Book Name', filename.replace('.pdf', '').replace('.epub', '')),
            author=metadata.get('Author Name', 'Unknown'),
            content=content,
            user_id=current_user.id
        )
        db.session.add(book)
        db.session.commit()

        # Process characters
        if metadata.get('Can_extract_characters', False):
            try:
                characters = ingest_book(file_path, file_type, content, metadata)
                
                if characters:
                    character_objects = [
                        Character(
                            name=char_name,
                            description=char_data["description"],
                            personality_traits=char_data["personality_traits"],
                            emotional_profile=char_data["emotional_profile"],
                            relationships=char_data["relationships"],
                            personality_summary=char_data["personality_summary"],
                            role=char_data.get("role", "Unknown"),
                            importance_level=char_data.get("importance_level", 1),
                            llm_persona_prompt=char_data.get("llm_persona_prompt", ""),
                            book_id=book.id
                        )
                        for char_name, char_data in characters.items()
                    ]
                    db.session.bulk_save_objects(character_objects)
                    db.session.commit()
            except Exception as e:
                logger.exception("Failed to process characters")
                return jsonify({'error': f'Failed to process characters: {str(e)}'}), 500
        else:
            logger.info("Book not suitable for character extraction")

        return jsonify({'success': True, 'book_id': book.id})

    except Exception as e:
        logger.exception("Upload failed")
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/libraries', methods=['GET', 'POST'])
@login_required
def libraries():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if not name:
            flash('Library name is required', 'danger')
            return redirect(url_for('libraries'))

        library = Library(name=name, description=description, user_id=current_user.id)
        db.session.add(library)
        db.session.commit()
        flash('Library created successfully', 'success')

    libraries = current_user.libraries.all()
    return render_template('libraries.html', libraries=libraries)

@app.route('/library/<int:library_id>')
@login_required
def library_detail(library_id):
    library = Library.query.get_or_404(library_id)
    if library.user_id != current_user.id:
        flash('Access denied', 'danger')
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
    try:
        book = Book.query.get_or_404(book_id)

        if book.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        # Delete related records first in the correct order
        # 1. Delete conversations for all characters in this book
        for character in book.characters:
            Conversation.query.filter_by(character_id=character.id).delete()
        
        # 2. Delete favorites
        Favorite.query.filter_by(book_id=book_id).delete()
        
        # 3. Delete characters
        Character.query.filter_by(book_id=book_id).delete()
        
        # 4. Remove book from libraries
        book.libraries = []
        
        # 5. Finally delete the book
        db.session.delete(book)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.exception("Failed to delete book")
        db.session.rollback()
        return jsonify({'error': str(e)}), 5000

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
        logger.exception("Failed to initialize character chat.")
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
        logger.exception("Failed to handle chat message.")
        return jsonify({'error': str(e)}), 500