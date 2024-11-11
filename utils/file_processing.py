from PyPDF2 import PdfReader
import re
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
from typing import Dict, List
from .character_analysis import (
    BasicCharacter,
    BasicCharacterList,
    CharacterDescription,
    CharacterDepth,
    analyze_book
)

def process_pdf_content(file) -> str:
    """Process PDF file and extract text content"""
    pdf_reader = PdfReader(file)
    content = ""
    for page in pdf_reader.pages:
        content += page.extract_text()
    return content

def extract_text_from_epub(epub_path: str) -> str:
    """Extract text content from EPUB file without requiring Pandoc"""
    book = epub.read_epub(epub_path)
    chapters = []

    # Get all items from the book
    items = list(book.get_items())

    for item in items:
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            try:
                # Get raw content
                content = item.get_content().decode('utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text(strip=True)
                
                if text:
                    chapters.append(text)

                for tag in soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    text = tag.get_text(strip=True)
                    if text:
                        chapters.append(text)

            except Exception as e:
                print(f"Error processing item: {str(e)}")

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
                        text = soup.get_text(strip=True)
                        if text:
                            chapters.append(text)
        except Exception as e:
            print(f"Error processing spine: {str(e)}")

    final_text = '\n\n'.join(chapters)
    return final_text

def extract_characters(content: str) -> Dict:
    """
    Extract and analyze characters from text content using the EnhancedBookAnalyzer approach.
    This function serves as a wrapper around the analyze_book function to maintain
    compatibility with existing code while using the enhanced analysis capabilities.
    """
    try:
        # Use the enhanced book analyzer to perform character analysis
        analysis_result = analyze_book(content)
        
        # Convert the analysis result into the expected format
        characters = {}
        
        # Combine basic info, descriptions, and character depth into unified character profiles
        for basic_char in analysis_result["basic_info"]:
            name = basic_char["name"]
            
            # Find matching description and depth info
            description = next(
                (desc for desc in analysis_result["descriptions"] if desc["name"] == name),
                None
            )
            depth = next(
                (dep for dep in analysis_result["character_depth"] if dep["name"] == name),
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
                "role": basic_char["role"],
                "importance_level": basic_char["importance_level"],
                "llm_persona_prompt": description["llm_persona_prompt"] if description else ""
            }
        
        return characters
        
    except Exception as e:
        print(f"Error in enhanced character extraction: {str(e)}")
        # Fallback to basic character extraction if enhanced analysis fails
        return _basic_character_extraction(content)

def _basic_character_extraction(content: str) -> Dict:
    """
    Fallback method for basic character extraction when enhanced analysis fails.
    """
    characters = {}
    name_pattern = r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)'
    potential_names = re.findall(name_pattern, content)
    
    for name in set(potential_names):
        if len(name.split()) >= 1:  # Only names with at least one word
            context = content[max(0, content.find(name)-100):content.find(name)+100]
            characters[name] = {
                "description": f"Character appearing in the context: {context}",
                "personality_traits": [],
                "emotional_profile": {},
                "relationships": [],
                "personality_summary": "Basic character identification",
                "role": "Unknown",
                "importance_level": 1,
                "llm_persona_prompt": f"You are {name}, a character mentioned in the story."
            }
    
    return characters
