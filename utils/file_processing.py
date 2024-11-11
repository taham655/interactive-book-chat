import PyPDF2
import re
from .personality_analyzer import analyze_personality

def process_pdf_content(file):
    """Process PDF file and extract text content"""
    pdf_reader = PyPDF2.PdfReader(file)
    content = ""
    for page in pdf_reader.pages:
        content += page.extract_text()
    return content

def extract_characters(content):
    """Enhanced character extraction with personality analysis"""
    characters = {}
    name_pattern = r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)'
    potential_names = re.findall(name_pattern, content)
    
    # Filter and create detailed character profiles
    for name in set(potential_names):
        if len(name.split()) >= 1:  # Only names with at least one word
            # Get surrounding context
            context = content[max(0, content.find(name)-500):content.find(name)+500]
            
            # Perform personality analysis
            personality_data = analyze_personality(content, name)
            
            characters[name] = {
                "description": f"Character appearing in the context: {context}",
                "personality_traits": personality_data["traits"],
                "emotional_profile": personality_data["emotions"],
                "relationships": personality_data["relationships"],
                "personality_summary": personality_data["summary"]
            }
    
    return characters
