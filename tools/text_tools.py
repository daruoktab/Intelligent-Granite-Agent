
import re
from typing import Dict, List, Union
from .base import BaseTool

class TextCounter(BaseTool):
    """Tool for counting words in text."""
    
    def __init__(self):
        super().__init__(
            name="count_words",
            description="Count words in text",
            parameters={
                'type': 'object',
                'required': ['text'],
                'properties': {
                    'text': {'type': 'string', 'description': 'Text to count words in'},
                },
            }
        )

    def execute(self, text: str) -> int:
        """Count the number of words in the given text."""
        if not text:
            return 0
        return len(text.split())

class TextAnalyzer(BaseTool):
    """Tool for analyzing text properties."""
    
    def __init__(self):
        super().__init__(
            name="analyze_text",
            description="Analyze text properties including character count, word count, sentence count, and average word length",
            parameters={
                'type': 'object',
                'required': ['text'],
                'properties': {
                    'text': {'type': 'string', 'description': 'Text to analyze'},
                },
            }
        )

    def execute(self, text: str) -> Dict[str, Union[int, float]]:
        """Analyze various properties of the given text."""
        if not text:
            return {
                "character_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "average_word_length": 0
            }
            
        # Count characters (excluding whitespace)
        char_count = len(text.replace(" ", ""))
        
        # Count words
        words = text.split()
        word_count = len(words)
        
        # Count sentences (simple approximation)
        sentence_count = len(re.split(r'[.!?]+', text)) - 1
        if sentence_count < 0:
            sentence_count = 0
            
        # Calculate average word length
        avg_word_length = sum(len(word) for word in words) / max(1, word_count)
        
        return {
            "character_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "average_word_length": round(avg_word_length, 2)
        }

class TextFormatter(BaseTool):
    """Tool for formatting text."""
    
    def __init__(self):
        super().__init__(
            name="format_text",
            description="Format text with various operations like uppercase, lowercase, title case, etc.",
            parameters={
                'type': 'object',
                'required': ['text', 'operation'],
                'properties': {
                    'text': {'type': 'string', 'description': 'Text to format'},
                    'operation': {
                        'type': 'string', 
                        'enum': ['uppercase', 'lowercase', 'titlecase', 'capitalize', 'strip'],
                        'description': 'Formatting operation to perform'
                    },
                },
            }
        )

    def execute(self, text: str, operation: str) -> str:
        """Format the text according to the specified operation."""
        if not text:
            return ""
            
        if operation == 'uppercase':
            return text.upper()
        elif operation == 'lowercase':
            return text.lower()
        elif operation == 'titlecase':
            return text.title()
        elif operation == 'capitalize':
            return text.capitalize()
        elif operation == 'strip':
            return text.strip()
        else:
            raise ValueError(f"Unknown operation: {operation}")