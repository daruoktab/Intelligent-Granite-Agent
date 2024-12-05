
import math
from .base import BaseTool

class ExpressionEvaluator(BaseTool):
    def __init__(self):
        super().__init__(
            name="evaluate_expression",
            description="Evaluate a mathematical expression",
            parameters={
                'type': 'object',
                'required': ['expression'],
                'properties': {
                    'expression': {'type': 'string', 'description': 'The expression to evaluate'},
                },
            }
        )

    def execute(self, expression: str) -> float:
        try:
            expression = expression.replace('^', '**')
            allowed_names = {name: obj for name, obj in math.__dict__.items() if not name.startswith("__")}
            allowed_names.update({'__builtins__': {}})
            return float(eval(expression, {"__builtins__": None}, allowed_names))
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {str(e)}")