from pydantic import BaseModel, Field
from typing import List

class BasicCharacter(BaseModel):
    name: str = Field(description="The character's full name")
    role: str = Field(description="The character's primary role (protagonist, antagonist, supporting)")
    plot_importance: str = Field(
        description="Detailed explanation of why this character is important to the plot"
    )
    importance_level: int = Field(
        description="Importance level 1-10, based on their impact on the main plot"
    )
    key_relationships: List[str] = Field(description="List of important relationships")

class BasicCharacterList(BaseModel):
    characters: List[BasicCharacter] = Field(description="List of identified characters")

class CharacterDescription(BaseModel):
    name: str
    detailed_description: str = Field(
        description="Comprehensive physical and personality description"
    )
    llm_persona_prompt: str = Field(
        description="A prompt section for emulating this character's personality"
    )

class CharacterDepth(BaseModel):
    name: str
    character_arc: str = Field(
        description="Detailed progression of character development"
    )
    personality_traits: List[str] = Field(
        description="List of personality traits with examples"
    )
    memorable_quotes: List[str] = Field(
        description="Key quotes that demonstrate character development",
    )

class CharacterDescriptionList(BaseModel):
    characters: List[CharacterDescription] = Field(description="List of character descriptions")

class CharacterDepthList(BaseModel):
    characters: List[CharacterDepth] = Field(description="List of character development analyses")

class CharacterAnalysis(BaseModel):
    basic_info: BasicCharacter
    description: CharacterDescription
    depth: CharacterDepth

class ChunkAnalysis(BaseModel):
    characters: List[CharacterAnalysis] = Field(description="Characters identified in this chunk")