import PyPDF2
import ebooklib
from ebooklib import epub
from typing import Dict
from .character_analysis import (
    analyze_book
)

from .models import (
    BasicCharacter,  # Add this import
    BasicCharacterList, 
    CharacterDescriptionList, 
    CharacterDepthList,
    CharacterAnalysis
)
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

def process_pdf_content(file) -> str:
    """Process PDF file and extract text content"""
    pdf_reader = PdfReader(file)
    content = ""
    for page in pdf_reader.pages:
        content += page.extract_text()
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

async def extract_characters(content: str) -> Dict:
    """
    Extract and analyze characters from text content using the EnhancedBookAnalyzer approach.
    This function serves as a wrapper around the analyze_book function to maintain
    compatibility with existing code while using the enhanced analysis capabilities.
    """
    try:
        # Use the enhanced book analyzer to perform character analysis
        analysis_result = await analyze_book(content)
        
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
                "role": basic_char.get("role", "Unknown"),  # Add role from basic info
                "importance_level": basic_char["importance_level"],
                "llm_persona_prompt": description["llm_persona_prompt"] if description else ""
            }
        
        return characters
        
    except Exception as e:
        print(f"Error in enhanced character extraction: {str(e)}")