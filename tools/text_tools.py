
from .base import BaseTool

class TextCounter(BaseTool):
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
        return len(text.split())