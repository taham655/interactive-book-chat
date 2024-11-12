# import os
# from openai import OpenAI
# from typing import Any, List, Dict
# import json
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_openai import ChatOpenAI
# from .character_analysis import create_character_prompt, get_character_details, BasicCharacterList, CharacterDescriptionList, CharacterDepthList

# # Initialize OpenAI client
# openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# def initialize_chat_model(model_name: str = "gemini-1.5-pro") -> Any:
#     """Initialize the chat model with the specified configuration"""
#     return ChatGoogleGenerativeAI(
#         model=model_name,
#         temperature=0.7
#     )

# def format_with_gpt(content: str, pass_number: int, model: Any) -> str:
#     """Use OpenAI's parse method to ensure output matches our Pydantic models"""
#     client = OpenAI()

#     model_map = {
#         1: BasicCharacterList,
#         2: CharacterDescriptionList,
#         3: CharacterDepthList
#     }

#     system_messages = {
#         1: "You are a character analysis expert. Format the content into the required structure.",
#         2: "You are a character analysis expert. Format the content into the required structure.",
#         3: "You are a character analysis expert. Format the content into the required structure. If no memorable quotes are available, use an empty array []."
#     }

#     try:
#         completion = client.beta.chat.completions.parse(
#             model="gpt-4-turbo-preview",
#             messages=[
#                 {"role": "system", "content": system_messages[pass_number]},
#                 {"role": "user", "content": f"Format this content into the required structure:\n\n{content}"}
#             ],
#             response_format=model_map[pass_number],
#         )

#         return json.dumps(completion.choices[0].message.parsed.model_dump(), indent=2)

#     except Exception as e:
#         print(f"Error formatting pass {pass_number}: {str(e)}")
#         print("Original content:", content)
#         raise

# def generate_character_response(
#     character_prompt: str,
#     messages: List[Dict[str, str]],
#     user_message: str,
#     model: Any = None
# ) -> str:
#     """
#     Generate a contextual response using the character's personality and conversation history.

#     Args:
#         character_prompt: The detailed character personality and behavior prompt
#         messages: List of previous conversation messages
#         user_message: The current user message
#         model: Optional model instance (will create new one if not provided)

#     Returns:
#         str: The character's response
#     """
#     if model is None:
#         model = initialize_chat_model()

#     # Prepare the conversation history
#     conversation = [{"role": "system", "content": character_prompt}]

#     # Add conversation history
#     for msg in messages:
#         conversation.append({
#             "role": msg["role"],
#             "content": msg["content"]
#         })

#     # Add the current user message
#     conversation.append({"role": "user", "content": user_message})

#     try:
#         # Generate response using the model
#         response = model.invoke(conversation)
#         return response.content

#     except Exception as e:
#         print(f"Error getting response: {str(e)}")
#         # Fallback to OpenAI if primary model fails
#         try:
#             fallback_model = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.7)
#             response = fallback_model.invoke(conversation)
#             return response.content
#         except Exception as e:
#             print(f"Fallback model also failed: {str(e)}")
#             return "I apologize, but I'm having trouble responding right now."

# def get_chatbot_response(prompt: str, messages: List[Dict[str, str]], model: Any) -> str:
#     """
#     Get response from the chatbot using the current character's persona.

#     Args:
#         prompt: The character's personality prompt
#         messages: The conversation history
#         model: The initialized chat model

#     Returns:
#         str: The generated response
#     """
#     conversation = [{"role": "system", "content": prompt}]

#     # Add conversation history
#     for msg in messages:
#         conversation.append({
#             "role": msg["role"],
#             "content": msg["content"]
#         })

#     try:
#         response = model.invoke(conversation)
#         return response.content
#     except Exception as e:
#         print(f"Error getting response: {str(e)}")
#         return None

# def initialize_chat(selected_character_full: str, character_data: Dict) -> tuple:
#     """
#     Initialize or reset chat with a new character.

#     Args:
#         selected_character_full: The selected character's full name and role
#         character_data: The complete character analysis data

#     Returns:
#         tuple: (character_prompt, character_name)
#     """
#     selected_name = selected_character_full.split(" - ")[0]
#     character_details = get_character_details(character_data, selected_name)
#     character_prompt = create_character_prompt(character_details)
#     return character_prompt, selected_name

# def get_character_details(character_data: Dict, selected_name: str) -> Dict:
#     """
#     Get all relevant details for the selected character.

#     Args:
#         character_data: The complete character analysis data
#         selected_name: The name of the selected character

#     Returns:
#         Dict: The character's complete details
#     """
#     basic_info = next((char for char in character_data['basic_info']
#                       if char['name'] == selected_name), None)
#     description = next((char for char in character_data['descriptions']
#                        if char['name'] == selected_name), None)
#     depth = next((char for char in character_data['character_depth']
#                  if char['name'] == selected_name), None)

#     return {
#         'basic_info': basic_info,
#         'description': description,
#         'depth': depth
#     }