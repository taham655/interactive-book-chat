import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
# from .character_analysis import analyze_book

async def process_pdf_content(file_path: str) -> Dict:
    """Process PDF file and extract character information."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text()

        return await analyze_book(text)
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise

def extract_text_from_epub(epub_path: str) -> str:
    """Extract text content from EPUB file."""
    book = epub.read_epub(epub_path)
    text = ''

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text += soup.get_text() + '\n'

    return text

async def extract_characters(file_path: str, file_type: str) -> Dict:
    """Extract character information from the uploaded file."""
    try:
        if file_type == 'pdf':
            return await process_pdf_content(file_path)
        elif file_type == 'epub':
            text = extract_text_from_epub(file_path)
            return await analyze_book(text)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        print(f"Error extracting characters: {str(e)}")
        raise
