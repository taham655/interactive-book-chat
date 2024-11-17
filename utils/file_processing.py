import PyPDF2
import ebooklib
from ebooklib import epub
import asyncio
import logging
from typing import Dict, Optional
from .character_analysis import analyze_book
from .character_models import (
    BasicCharacter,
    BasicCharacterList, 
    CharacterDescriptionList, 
    CharacterDepthList,
    CharacterAnalysis
)
from .character_analysis import EnhancedBookAnalyzer
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from models import db, BookAnalysis
import json
import os
import logging
from openai import OpenAI
import re
import time
import sqlalchemy.exc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_pdf_content(file) -> str:
    """Process PDF file and extract text content"""
    pdf_reader = PdfReader(file)
    content = ""
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            content += text
    return content

def extract_text_from_epub(epub_path: str) -> str:
    """Extract text content from EPUB file."""
    book = epub.read_epub(epub_path)
    text = ''
    chapters = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            try:
                # Get raw content
                content = item.get_content().decode('utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text(separator=' ', strip=True)
                
                if text:
                    chapters.append(text)

                # Extract text from specific tags
                for tag in soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    text = tag.get_text(separator=' ', strip=True)
                    if text:
                        chapters.append(text)

            except Exception as e:
                logger.error(f"Error processing item: {str(e)}")

    # If still no content, try spine items
    if not chapters:
        try:
            for spine_item in book.spine:
                if isinstance(spine_item, tuple):
                    item_id = spine_item[0]
                    item = book.get_item_with_id(item_id)
                    if item:
                        content = item.get_content().decode('utf-8')
                        soup = BeautifulSoup(content, 'html.parser')
                        text = soup.get_text(separator=' ', strip=True)
                        if text:
                            chapters.append(text)
        except Exception as e:
            logger.error(f"Error processing spine items: {str(e)}")

    return ' '.join(chapters)

import re
import time

def analyze_book_metadata_sync(content: str, max_retries: int = 3, retry_delay: float = 1.0) -> Dict:
    """
    Analyze the first 15 pages of a book to extract metadata synchronously.

    Args:
        content (str): The text content of the first 15 pages of the book.
        max_retries (int): Maximum number of retries for failed JSON parsing.
        retry_delay (float): Delay between retries in seconds.

    Returns:
        Dict: A dictionary containing the extracted metadata:
            - "Book Name" (str)
            - "Author Name" (str)
            - "Is Religious_Scripture" (bool)
            - "is_fictional" (bool)
            - "Can_extract_characters" (bool)
    """
    prompt = (
        "You are a specialized book metadata analyzer. Your task is to carefully analyze the provided text "
        "and extract specific metadata. Follow these guidelines strictly:\n\n"
        
        "1. Religious Text Identification:\n"
        "   - Check for religious terminology, themes, and references\n"
        "   - Look for sacred or spiritual content\n"
        "   - Identify religious teachings, prayers, or scriptures\n"
        "   - Common religious texts include: Bible, Quran, Torah, Bhagavad Gita, etc.\n\n"
        
        "2. Book Name and Author:\n"
        "   - Extract ONLY from clear title/author mentions\n"
        "   - Do NOT guess or default to famous books\n"
        "   - If uncertain, use 'Unknown' for either field\n"
        "   - Look for copyright pages, title pages, or headers\n\n"
        
        "3. Fiction vs Non-Fiction:\n"
        "   - Analyze writing style and content type\n"
        "   - Look for narrative elements vs factual presentation\n"
        "   - Consider genre indicators and context\n\n"
        
        "4. Character Analysis Potential:\n"
        "   - Evaluate presence of distinct personalities or figures\n"
        "   - Consider if the text focuses on individuals or concepts\n"
        "   - Religious texts may have historical figures but aren't suitable for character analysis\n\n"
        
        "Return ONLY a JSON object with these fields:\n"
        "{\n"
        '  "Book Name": string (use "Unknown" if not clearly stated),\n'
        '  "Author Name": string (use "Unknown" if not clearly stated),\n'
        '  "Is Religious_Scripture": boolean (true for any religious or spiritual text),\n'
        '  "is_fictional": boolean (false for religious texts, historical accounts, or educational material),\n'
        '  "Can_extract_characters": boolean (should be false for religious texts)\n'
        "}\n\n"
        
        "Important Rules:\n"
        "1. Never default to famous books - if unsure, use 'Unknown'\n"
        "2. Religious texts should ALWAYS have Is_Religious_Scripture=true and Can_extract_characters=false\n"
        "3. Be conservative in judgments - when in doubt, mark fields as Unknown/false\n"
        "4. Analyze the actual content, not just the first few lines\n\n"
        
        "Analyze the following text and provide only the JSON response:"
    )

    try:
        client = OpenAI()

        for attempt in range(1, max_retries + 1):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an assistant that extracts book metadata."},
                    {"role": "user", "content": prompt + "\n\n" + content}
                ],
                temperature=0.0,
                max_tokens=500
            )

            # Extract the content from the response
            raw_response = response.choices[0].message.content.strip()
            logger.info(f"Raw OpenAI response (Attempt {attempt}): {raw_response}")

            # Attempt to extract JSON using regex
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                try:
                    metadata = json.loads(json_str)
                    
                    # Validate and ensure all required fields are present
                    required_fields = {
                        "Book Name": str,
                        "Author Name": str,
                        "Is Religious_Scripture": bool,
                        "is_fictional": bool,
                        "Can_extract_characters": bool
                    }

                    for field, field_type in required_fields.items():
                        if field not in metadata:
                            raise ValueError(f"Missing field in response: {field}")
                        if not isinstance(metadata[field], field_type):
                            raise TypeError(f"Incorrect type for field '{field}': Expected {field_type.__name__}, got {type(metadata[field]).__name__}")

                    return metadata

                except (json.JSONDecodeError, ValueError, TypeError) as parse_err:
                    logger.error(f"Attempt {attempt}: JSON parsing error: {parse_err}")
                    logger.debug(f"Failed JSON string: {json_str}")
            else:
                logger.error(f"Attempt {attempt}: Could not find JSON object in the response.")

            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

        logger.error("All attempts to parse JSON from OpenAI response failed.")
        return {}

    except Exception as e:
        logger.error(f"Error analyzing book metadata: {e}")
        return {}

def extract_characters(content: str) -> Dict:
    """
    Extract and analyze characters from text content using the EnhancedBookAnalyzer approach.
    """
    try:
        # Create analyzer instance
        analyzer = EnhancedBookAnalyzer()
        
        # Run the analysis synchronously using asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(analyzer.analyze_full_text(content))
        loop.close()

        # Convert the analysis result into the expected format
        characters = {}

        # Combine basic info, descriptions, and character depth into unified character profiles
        for basic_char in result["basic_info"]:
            name = basic_char["name"]

            # Find matching description and depth info
            description = next(
                (desc for desc in result["descriptions"] if desc["name"] == name),
                None
            )
            depth = next(
                (dep for dep in result["character_depth"] if dep["name"] == name),
                None
            )

            # Create comprehensive character profile
            characters[name] = {
                "description": description["detailed_description"] if description else "",
                "personality_traits": depth["personality_traits"] if depth else [],
                "emotional_profile": {
                    "character_arc": depth["character_arc"] if depth else "",
                    "memorable_quotes": depth["memorable_quotes"] if depth else []
                },
                "relationships": basic_char["key_relationships"],
                "personality_summary": basic_char["plot_importance"],
                "role": basic_char.get("role", "Unknown"),
                "importance_level": basic_char["importance_level"],
                "llm_persona_prompt": description["llm_persona_prompt"] if description else ""
            }

        return characters

    except Exception as e:
        logger.error(f"Error in enhanced character extraction: {e}")
        return {}

def ingest_book(file_path: str, file_type: str, content: str, metadata: Dict) -> Dict:
    """
    Ingest a book file and extract character information, with caching support.
    """
    try:
        if not metadata.get('Can_extract_characters', False):
            logger.info("Book not suitable for character extraction")
            return {}
            
        book_name = metadata.get('Book Name')
        author_name = metadata.get('Author Name')
        
        if book_name == 'Unknown' or author_name == 'Unknown':
            logger.warning("Could not determine book or author name")
            return perform_full_analysis_sync(content)
            
        # Check for existing analysis
        existing_analysis = BookAnalysis.query.filter_by(
            book_name=book_name,
            author_name=author_name
        ).first()
        
        if existing_analysis:
            logger.info(f"Found existing analysis for {book_name} by {author_name}")
            return existing_analysis.character_analysis
            
        # If no existing analysis, perform full analysis
        character_analysis = perform_full_analysis_sync(content)
        
        try:
            # Try to create new analysis
            new_analysis = BookAnalysis(
                book_name=book_name,
                author_name=author_name,
                character_analysis=character_analysis
            )
            db.session.add(new_analysis)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            # If another process created the analysis in the meantime
            db.session.rollback()
            # Fetch the existing analysis
            existing_analysis = BookAnalysis.query.filter_by(
                book_name=book_name,
                author_name=author_name
            ).first()
            if existing_analysis:
                return existing_analysis.character_analysis
            
        return character_analysis
        
    except Exception as e:
        logger.exception("Error in book ingestion")
        raise

def perform_full_analysis_sync(content: str) -> Dict:
    """
    Synchronous wrapper for the async analysis process.
    """
    try:
        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async analysis
        result = loop.run_until_complete(perform_full_analysis(content))
        
        # Clean up
        loop.close()
        
        return result
        
    except Exception as e:
        logger.exception("Error in full analysis sync wrapper")
        raise

async def perform_full_analysis(content: str) -> Dict:
    """
    Perform full three-pass analysis of book content.
    """
    try:
        analyzer = EnhancedBookAnalyzer()
        result = await analyzer.analyze_full_text(content)
        
        # Convert the analysis result into the expected character dictionary format
        characters = {}
        
        # Process each character from the analysis
        for basic_char in result.get("basic_info", []):
            name = basic_char["name"]
            
            # Find matching description and depth info
            description = next(
                (desc for desc in result.get("descriptions", []) if desc["name"] == name),
                None
            )
            depth = next(
                (dep for dep in result.get("character_depth", []) if dep["name"] == name),
                None
            )
            
            # Create comprehensive character profile
            characters[name] = {
                "description": description["detailed_description"] if description else "",
                "personality_traits": depth["personality_traits"] if depth else [],
                "emotional_profile": {
                    "character_arc": depth["character_arc"] if depth else "",
                    "memorable_quotes": depth["memorable_quotes"] if depth else []
                },
                "relationships": basic_char.get("key_relationships", []),
                "personality_summary": basic_char.get("plot_importance", ""),
                "role": basic_char.get("role", "Unknown"),
                "importance_level": basic_char.get("importance_level", 1),
                "llm_persona_prompt": description["llm_persona_prompt"] if description else ""
            }
            
        return characters
        
    except Exception as e:
        logger.exception("Error in full analysis")
        raise