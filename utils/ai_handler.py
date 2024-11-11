import os
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_character_response(character_name: str, character_description: str, 
                              book_content: str, user_message: str) -> str:
    """Generate a contextual response using OpenAI's API"""
    
    # Create a system prompt that defines the character's personality
    system_prompt = f"""You are {character_name}, a character from a book. 
    Here's your background: {character_description}
    
    Respond to the user's message in character, maintaining consistency with your background 
    and the book's content. Keep responses concise and engaging."""
    
    # Add relevant book content for context (limited to avoid token limits)
    context = book_content[:1000] if book_content else ""
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 for complex character interactions
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context from the book: {context}"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150  # Limit response length
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # Fallback response in case of API errors
        return f"As {character_name}, I apologize, but I'm having trouble formulating a response right now."
