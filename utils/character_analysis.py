from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import json
import asyncio
import aiofiles
from .models import (
    BasicCharacter,
    BasicCharacterList, 
    CharacterDescriptionList, 
    CharacterDepthList,
    CharacterAnalysis,
    ChunkAnalysis
)
from .ai_handler import (
    format_with_gpt,
    initialize_chat_model
)

from .prompts import (
    create_character_prompt,
    first_pass_template,
    second_pass_template,
    third_pass_template
)
from typing import Dict, List, Optional, Any

class EnhancedBookAnalyzer:
    def __init__(self, primary_model="gemini-1.5-pro", fallback_model="gpt-4o-mini"):
        self.primary_model = ChatGoogleGenerativeAI(model=primary_model, temperature=0.7)
        self.fallback_model = ChatOpenAI(model=fallback_model, temperature=0.7)
        self.basic_parser = PydanticOutputParser(pydantic_object=BasicCharacterList)
        self.description_parser = PydanticOutputParser(pydantic_object=CharacterDescriptionList)
        self.depth_parser = PydanticOutputParser(pydantic_object=CharacterDepthList)
        self.using_fallback = False

        # Create prompts
        self.first_pass_prompt = PromptTemplate(
            template=first_pass_template,
            input_variables=["book_text"],
            partial_variables={"format_instructions": self.basic_parser.get_format_instructions()}
        )
        self.second_pass_prompt = PromptTemplate(
            template=second_pass_template,
            input_variables=["character_list"],
            partial_variables={"format_instructions": self.description_parser.get_format_instructions()}
        )
        self.third_pass_prompt = PromptTemplate(
            template=third_pass_template,
            input_variables=["character_list"],
            partial_variables={"format_instructions": self.depth_parser.get_format_instructions()}
        )

    async def analyze_full_text(self, book_text: str) -> Dict:
        """Primary analysis method that handles both direct and chunked processing."""
        try:
            # First Pass: Character Identification
            basic_characters = await self._first_pass_analysis(book_text)

            # Convert to character list for subsequent passes
            character_list = [
                {"name": char.name, "role": char.role}
                for char in basic_characters.characters
            ]

            # Use the appropriate model for subsequent passes
            model = self.fallback_model if self.using_fallback else self.primary_model

            # Run second and third pass analyses concurrently
            character_descriptions, character_depth = await asyncio.gather(
                self._second_pass_analysis(character_list, model),
                self._third_pass_analysis(character_list, model)
            )

            return self._format_result(
                basic_characters,
                character_descriptions,
                character_depth
            )

        except Exception as e:
            print(f"Error during character analysis: {str(e)}")
            raise

    async def _first_pass_analysis(self, book_text: str) -> BasicCharacterList:
        """Perform first pass analysis with fallback to chunked processing if needed."""
        try:
            # Try with primary model first
            first_pass = await self.primary_model.ainvoke(
                self.first_pass_prompt.format(book_text=book_text)
            )

            # Check for empty/blocked response
            if not first_pass.content or first_pass.content.strip() == "":
                print("Switching to advanced analysis method for better results...")
                self.using_fallback = True
                return await self._chunked_first_pass(book_text)

            # Process primary model response
            formatted_response = await format_with_gpt(
                first_pass.content, 
                1
            )
            basic_characters = self.basic_parser.parse(formatted_response)
            return basic_characters

        except Exception as e:
            print("Switching to advanced analysis method...")
            self.using_fallback = True
            return await self._chunked_first_pass(book_text)

    async def _chunked_first_pass(self, book_text: str) -> BasicCharacterList:
        """Process first pass in chunks using fallback model."""
        words = book_text.split()
        chunk_size = 50000
        chunks = [
            ' '.join(words[i:i + chunk_size])
            for i in range(0, len(words), chunk_size)
        ]

        total_chunks = len(chunks)
        all_characters = {}  # Using dict for deduplication

        for i, chunk in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{total_chunks}")
            try:
                # Process chunk to find characters
                first_pass = await self.fallback_model.ainvoke(
                    self.first_pass_prompt.format(book_text=chunk)
                )
                # Format the fallback model response
                formatted_response = await format_with_gpt(
                    first_pass.content, 
                    1
                )
                chunk_characters = self.basic_parser.parse(formatted_response)

                # Merge characters from this chunk
                for char in chunk_characters.characters:
                    if char.name in all_characters:
                        # Update existing character info
                        self._merge_character_basic_info(all_characters[char.name], char)
                    else:
                        # Add new character
                        all_characters[char.name] = char

                await asyncio.sleep(30)  # Small delay to prevent rate limiting

            except Exception as e:
                print(f"Had trouble with chunk {i}, but continuing: {str(e)}")
                continue

        return BasicCharacterList(characters=list(all_characters.values()))

    async def _second_pass_analysis(self, character_list: List[Dict], model) -> CharacterDescriptionList:
        """Perform second pass analysis for character descriptions."""
        second_pass = await model.ainvoke(
            self.second_pass_prompt.format(character_list=str(character_list))
        )

        # Format response
        formatted_response = await format_with_gpt(second_pass.content, 2)
        character_descriptions = self.description_parser.parse(formatted_response)
        return character_descriptions

    async def _third_pass_analysis(self, character_list: List[Dict], model) -> CharacterDepthList:
        """Perform third pass analysis for character depth."""
        third_pass = await model.ainvoke(
            self.third_pass_prompt.format(character_list=str(character_list))
        )

        # Format response
        formatted_response = await format_with_gpt(third_pass.content, 3)
        character_depth = self.depth_parser.parse(formatted_response)
        return character_depth

    def _merge_character_basic_info(self, existing: BasicCharacter, new: BasicCharacter) -> None:
        """Merge basic character information from chunks."""
        # Update importance level to highest found
        existing.importance_level = max(existing.importance_level, new.importance_level)

        # Keep longer plot importance description
        if len(new.plot_importance) > len(existing.plot_importance):
            existing.plot_importance = new.plot_importance

        # Merge relationships without duplicates
        existing.key_relationships = list(set(existing.key_relationships + new.key_relationships))

    def _format_result(self, basic_chars, char_descriptions, char_depth) -> Dict:
        """Format the final result."""
        return {
            "basic_info": [
                char.model_dump()
                for char in basic_chars.characters
            ],
            "descriptions": [
                char.model_dump()
                for char in char_descriptions.characters
            ],
            "character_depth": [
                char.model_dump()
                for char in char_depth.characters
            ]
        }

async def analyze_book(book_text: str, primary_model: str = "gemini-1.5-pro", 
                      fallback_model: str = "gpt-4o-mini") -> Dict:
    """Main function to analyze a book's characters with fallback support."""
    analyzer = EnhancedBookAnalyzer(
        primary_model=primary_model,
        fallback_model=fallback_model
    )
    
    try:
        result = await analyzer.analyze_full_text(book_text)
        
        # Save to JSON file asynchronously
        async with aiofiles.open('character_analysis.json', 'w', encoding='utf-8') as f:
            await f.write(json.dumps(result, indent=4, ensure_ascii=False))
            
        return result
        
    except Exception as e:
        print(f"Error during character analysis: {str(e)}")
        raise

def initialize_chat(selected_character: str, character_data: Dict = None) -> tuple[str, str]:
    """Initialize chat with a selected character"""
    if not character_data:
        try:
            with open('character_analysis.json', 'r', encoding='utf-8') as f:
                character_data = json.load(f)
        except FileNotFoundError:
            raise ValueError("Character analysis file not found")

    character_name = selected_character.split(" - ")[0]
    character_details = get_character_details(character_data, character_name)
    
    if not character_details:
        raise ValueError(f"Character {character_name} not found in analysis")
        
    character_prompt = create_character_prompt(character_details)
    
    return character_prompt, character_name

def get_chatbot_response(
    prompt: str,
    messages: List[Dict[str, str]],
    model: Any,
    temperature: float = 0.7
) -> Optional[str]:
    """Generate a response from the chatbot"""
    try:
        # Format the conversation history
        formatted_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
        
        # Add the system prompt at the beginning
        formatted_messages.insert(0, {
            "role": "system",
            "content": prompt
        })
        
        # Get completion from the model
        response = model.invoke(formatted_messages)
        
        return response.content if response else None
        
    except Exception as e:
        print(f"Error getting chatbot response: {str(e)}")
        return None

def get_character_details(character_data: Dict, character_name: str) -> Optional[Dict]:
    """Extract character details from the analysis data"""
    try:
        # Search in basic_info
        basic_info = next(
            (char for char in character_data.get("basic_info", [])
             if char["name"] == character_name),
            None
        )
        
        # Search in character descriptions
        description = next(
            (char for char in character_data.get("character_descriptions", [])
             if char["name"] == character_name),
            None
        )
        
        # Search in character depth
        depth = next(
            (char for char in character_data.get("character_depth", [])
             if char["name"] == character_name),
            None
        )
        
        if basic_info and description and depth:
            return {
                "basic_info": basic_info,
                "description": description,
                "depth": depth
            }
        return None
        
    except Exception as e:
        print(f"Error getting character details: {str(e)}")
        return None

pass 