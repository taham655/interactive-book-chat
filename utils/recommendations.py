import numpy as np
from collections import Counter
from models import Book, User, Character, Favorite, Library
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict

async def calculate_book_similarity(book1: Book, book2: Book) -> float:
    """Calculate similarity between two books based on character traits"""
    if not (await book1.characters.count() and await book2.characters.count()):
        return 0.0
    
    # Combine all character traits and emotional profiles
    async def get_book_profile(book: Book) -> Dict:
        profile = Counter()
        async for character in book.characters:
            if character.personality_traits:
                profile.update(character.personality_traits)
            if character.emotional_profile:
                profile.update(character.emotional_profile)
        return profile
    
    profile1 = await get_book_profile(book1)
    profile2 = await get_book_profile(book2)
    
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

async def get_recommendations(user: User, session: AsyncSession, limit: int = 5) -> List[Book]:
    """Get book recommendations based on user preferences and reading history"""
    # Get user's favorite books and books in libraries
    favorite_books = [fav.book for fav in user.favorites if fav.book_id is not None]
    library_books = []
    for library in user.libraries:
        books = await library.books.all()
        library_books.extend(books)
    
    # Combine user's books for preference analysis
    user_books = set(favorite_books + library_books)
    
    if not user_books:
        # If user has no preferences, return most popular books
        result = await session.execute(
            Book.query.join(Favorite)
            .group_by(Book.id)
            .order_by(func.count(Favorite.id).desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    # Get all other books
    result = await session.execute(
        Book.query.filter(Book.id.notin_([book.id for book in user_books]))
    )
    all_books = result.scalars().all()
    
    # Calculate similarity scores
    book_scores = []
    for candidate_book in all_books:
        total_similarity = 0
        for user_book in user_books:
            similarity = await calculate_book_similarity(user_book, candidate_book)
            # Weigh favorites higher
            weight = 1.5 if user_book in favorite_books else 1.0
            total_similarity += similarity * weight
        
        if len(user_books) > 0:
            avg_similarity = total_similarity / len(user_books)
            book_scores.append((candidate_book, avg_similarity))
    
    # Sort by similarity score and return top recommendations
    recommended_books = sorted(book_scores, key=lambda x: x[1], reverse=True)
    return [book for book, _ in recommended_books[:limit]]
