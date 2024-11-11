# import re
# from textblob import TextBlob
# import nltk
# from nltk.tokenize import sent_tokenize
# from collections import Counter

# def download_nltk_data():
#     """Download required NLTK data"""
#     try:
#         nltk.data.find('tokenizers/punkt')
#     except LookupError:
#         nltk.download('punkt')
#         nltk.download('averaged_perceptron_tagger')

# # Download required NLTK data
# download_nltk_data()

# def analyze_personality(text, character_name):
#     """
#     Analyze character personality from text context
#     Returns a dictionary of personality traits and supporting evidence
#     """
#     # Normalize character name for better matching
#     name_pattern = re.compile(rf'\b{re.escape(character_name)}\b', re.IGNORECASE)
    
#     # Find sentences containing character mentions
#     character_sentences = []
#     for sentence in sent_tokenize(text):
#         if name_pattern.search(sentence):
#             character_sentences.append(sentence)
    
#     if not character_sentences:
#         return {
#             "traits": {},
#             "emotions": {},
#             "relationships": [],
#             "summary": f"Insufficient context found for {character_name}"
#         }
    
#     # Analyze sentiment and subjectivity
#     sentiment_scores = []
#     for sentence in character_sentences:
#         blob = TextBlob(sentence)
#         sentiment_scores.append(blob.sentiment.polarity)
    
#     avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    
#     # Extract personality traits based on context
#     traits = analyze_traits(character_sentences)
#     emotions = analyze_emotions(character_sentences)
#     relationships = analyze_relationships(text, character_name)
    
#     # Generate personality summary
#     summary = generate_personality_summary(traits, emotions, avg_sentiment, character_name)
    
#     return {
#         "traits": traits,
#         "emotions": emotions,
#         "relationships": relationships,
#         "summary": summary
#     }

# def analyze_traits(sentences):
#     """Extract personality traits from sentences"""
#     trait_indicators = {
#         'brave': ['brave', 'courageous', 'fearless', 'bold'],
#         'intelligent': ['smart', 'intelligent', 'clever', 'wise', 'brilliant'],
#         'kind': ['kind', 'gentle', 'caring', 'compassionate', 'helpful'],
#         'determined': ['determined', 'persistent', 'resolute', 'steadfast'],
#         'loyal': ['loyal', 'faithful', 'devoted', 'dedicated']
#     }
    
#     found_traits = Counter()
    
#     for sentence in sentences:
#         sentence = sentence.lower()
#         for trait, indicators in trait_indicators.items():
#             if any(indicator in sentence for indicator in indicators):
#                 found_traits[trait] += 1
    
#     return dict(found_traits)

# def analyze_emotions(sentences):
#     """Analyze emotional patterns in sentences"""
#     emotion_words = {
#         'joy': ['happy', 'joyful', 'delighted', 'pleased'],
#         'anger': ['angry', 'furious', 'enraged', 'mad'],
#         'fear': ['afraid', 'scared', 'fearful', 'terrified'],
#         'sadness': ['sad', 'depressed', 'unhappy', 'miserable']
#     }
    
#     emotions = Counter()
    
#     for sentence in sentences:
#         sentence = sentence.lower()
#         for emotion, indicators in emotion_words.items():
#             if any(indicator in sentence for indicator in indicators):
#                 emotions[emotion] += 1
    
#     return dict(emotions)

# def analyze_relationships(text, character_name):
#     """Analyze character relationships"""
#     sentences = sent_tokenize(text)
#     relationships = []
    
#     # Find sentences with character interactions
#     name_pattern = re.compile(rf'\b{re.escape(character_name)}\b', re.IGNORECASE)
    
#     for sentence in sentences:
#         if name_pattern.search(sentence):
#             # Look for other proper nouns that might be character names
#             blob = TextBlob(sentence)
#             for word, tag in blob.tags:
#                 if tag == 'NNP' and word != character_name:
#                     relationships.append(word)
    
#     return list(set(relationships))

# def generate_personality_summary(traits, emotions, sentiment, character_name):
#     """Generate a natural language summary of personality analysis"""
#     summary_parts = []
    
#     # Trait summary
#     if traits:
#         top_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)[:3]
#         trait_text = ", ".join(trait for trait, _ in top_traits)
#         summary_parts.append(f"{character_name} appears to be {trait_text}")
    
#     # Emotional tendency
#     if emotions:
#         dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
#         summary_parts.append(f"often expressing {dominant_emotion}")
    
#     # Overall sentiment
#     sentiment_desc = "positive" if sentiment > 0.1 else "negative" if sentiment < -0.1 else "neutral"
#     summary_parts.append(f"with a generally {sentiment_desc} disposition")
    
#     return " ".join(summary_parts)
