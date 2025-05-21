
import re
from typing import Dict, List, Union
from .base import BaseTool

class TextCounter(BaseTool):
    """Tool for counting words in text."""
    
    def __init__(self):
        super().__init__(
            name="count_words",
            description="Count words in text",
            parameters={ # type: ignore
                'type': 'object',
                'required': ['text'],
                'properties': {
                    'text': {'type': 'string', 'description': 'Text to count words in'},
                },
            }
        )

    def execute(self, **kwargs: any) -> int:
        """Count the number of words in the given text."""
        text = kwargs.get('text')
        if not isinstance(text, str) or not text: # Ensure text is a non-empty string
            # Consider raising ValueError or returning 0 based on desired behavior for empty/invalid text
            return 0 # Or raise ValueError("Missing or invalid 'text' (string) argument.")
        return len(text.split())

class TextAnalyzer(BaseTool):
    """Tool for analyzing text properties."""
    
    def __init__(self):
        super().__init__(
            name="analyze_text",
            description="Analyze text properties including character count, word count, sentence count, and average word length",
            parameters={ # type: ignore
                'type': 'object',
                'required': ['text'],
                'properties': {
                    'text': {'type': 'string', 'description': 'Text to analyze'},
                },
            }
        )

    def execute(self, **kwargs: any) -> Dict[str, Union[int, float]]:
        """Analyze various properties of the given text."""
        text = kwargs.get('text')
        if not isinstance(text, str) or not text:
            # Consider raising ValueError or returning a default dict
            return { # Default for empty/invalid text
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
            parameters={ # type: ignore
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

    def execute(self, **kwargs: any) -> str:
        """Format the text according to the specified operation."""
        text = kwargs.get('text')
        operation = kwargs.get('operation')

        if not isinstance(text, str): # Allow empty string for text, but check type
            raise ValueError("Missing or invalid 'text' (string) argument.")
        if not isinstance(operation, str) or not operation:
            raise ValueError("Missing or invalid 'operation' (string) argument.")

        if not text and operation != 'strip': # Most operations on empty string return empty string
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

class SpecificLetterCounter(BaseTool):
    """Tool for counting occurrences of a specific letter or substring in text."""

    def __init__(self):
        super().__init__(
            name="count_specific_letter",
            description="Count occurrences of a specific letter or substring within a given text.",
            parameters={ # type: ignore
                'type': 'object',
                'required': ['text', 'letter_to_count'],
                'properties': {
                    'text': {'type': 'string', 'description': 'The text to search within.'},
                    'letter_to_count': {'type': 'string', 'description': 'The specific letter or substring to count.'},
                },
            }
        )

    def execute(self, **kwargs: any) -> int:
        """Count occurrences of the specified letter/substring in the text."""
        text = kwargs.get('text')
        letter_to_count = kwargs.get('letter_to_count')

        if not isinstance(text, str):
            raise ValueError("Missing or invalid 'text' (string) argument.")
        if not isinstance(letter_to_count, str) or not letter_to_count: # Must be non-empty string
            raise ValueError("Missing or invalid 'letter_to_count' (non-empty string) argument.")
        
        return text.count(letter_to_count)
