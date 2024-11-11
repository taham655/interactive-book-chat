import numpy as np
from collections import Counter
from models import Book, User, Character, Favorite, Library
from sqlalchemy import func
from typing import List, Dict

def calculate_book_similarity(book1: Book, book2: Book) -> float:
    """Calculate similarity between two books based on character traits"""
    if not (book1.characters.count() and book2.characters.count()):
        return 0.0
    
    # Combine all character traits and emotional profiles
    def get_book_profile(book: Book) -> Dict:
        profile = Counter()
        for character in book.characters:
            if character.personality_traits:
                profile.update(character.personality_traits)
            if character.emotional_profile:
                profile.update(character.emotional_profile)
        return profile
    
    profile1 = get_book_profile(book1)
    profile2 = get_book_profile(book2)
    
    # Calculate cosine similarity between profiles
    if not (profile1 and profile2):
        return 0.0
        
    common_traits = set(profile1.keys()) & set(profile2.keys())
    if not common_traits:
        return 0.0
        
    vec1 = np.array([profile1[trait] for trait in common_traits])
    vec2 = np.array([profile2[trait] for trait in common_traits])
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

def get_recommendations(user: User, limit: int = 5) -> List[Book]:
    """Get book recommendations based on user preferences and reading history"""
    # Get user's favorite books and books in libraries
    favorite_books = [fav.book for fav in user.favorites if fav.book_id is not None]
    library_books = []
    for library in user.libraries:
        library_books.extend(library.books.all())
    
    # Combine user's books for preference analysis
    user_books = set(favorite_books + library_books)
    
    if not user_books:
        # If user has no preferences, return most popular books
        return Book.query.join(Favorite).group_by(Book.id)\
            .order_by(func.count(Favorite.id).desc())\
            .limit(limit).all()
    
    # Get all other books
    all_books = Book.query.filter(Book.id.notin_([book.id for book in user_books])).all()
    
    # Calculate similarity scores
    book_scores = []
    for candidate_book in all_books:
        total_similarity = 0
        for user_book in user_books:
            similarity = calculate_book_similarity(user_book, candidate_book)
            # Weigh favorites higher
            weight = 1.5 if user_book in favorite_books else 1.0
            total_similarity += similarity * weight
        
        if len(user_books) > 0:
            avg_similarity = total_similarity / len(user_books)
            book_scores.append((candidate_book, avg_similarity))
    
    # Sort by similarity score and return top recommendations
    recommended_books = sorted(book_scores, key=lambda x: x[1], reverse=True)
    return [book for book, _ in recommended_books[:limit]]
