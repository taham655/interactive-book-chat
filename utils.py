import PyPDF2
import re

def process_pdf_content(file):
    """Process PDF file and extract text content"""
    pdf_reader = PyPDF2.PdfReader(file)
    content = ""
    for page in pdf_reader.pages:
        content += page.extract_text()
    return content

def extract_characters(content):
    """Simple character extraction logic (placeholder)"""
    # This is a simplified version - in production you'd want more sophisticated NLP
    characters = {}
    name_pattern = r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)'
    potential_names = re.findall(name_pattern, content)
    
    # Filter and create basic character profiles
    for name in set(potential_names):
        if len(name.split()) >= 1:  # Only names with at least one word
            context = content[max(0, content.find(name)-100):content.find(name)+100]
            characters[name] = f"Character appearing in the context: {context}"
    
    return characters
