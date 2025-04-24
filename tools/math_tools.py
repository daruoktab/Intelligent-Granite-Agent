
import math
import re
from typing import Dict, Any, Union, Optional
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
                    'expression': {'type': 'string', 'description': 'The mathematical expression to evaluate'},
                },
            }
        )
        # Define allowed operators and functions
        self.operators = {'+', '-', '*', '/', '**', '^', '%', '(', ')', '.'}
        self.allowed_functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'floor': math.floor,
            'ceil': math.ceil,
            'pi': math.pi,
            'e': math.e
        }
        
    def _is_safe_expression(self, expression: str) -> bool:
        """Check if the expression contains only allowed characters and functions."""
        # Remove all whitespace
        expression = expression.replace(' ', '')
        
        # Replace ^ with ** for exponentiation
        expression = expression.replace('^', '**')
        
        # Check for allowed functions and constants
        for func in self.allowed_functions.keys():
            expression = expression.replace(func, '')
        
        # Check for digits and operators
        pattern = r'^[0-9\+\-\*\/\(\)\.\%\*]*$'
        return bool(re.match(pattern, expression))
    
    def _parse_and_evaluate(self, expression: str) -> float:
        """Parse and evaluate the expression using a safer approach than eval()."""
        # Replace ^ with ** for exponentiation
        expression = expression.replace('^', '**')
        
        # Create a safe namespace with only allowed functions and constants
        safe_dict: Dict[str, Any] = {
            '__builtins__': None,
            **self.allowed_functions
        }
        
        # Evaluate the expression in the restricted environment
        return float(eval(expression, {"__builtins__": None}, safe_dict))

    def execute(self, expression: str) -> float:
        """Execute the mathematical expression evaluation."""
        try:
            # Validate the expression
            if not self._is_safe_expression(expression):
                raise ValueError("Expression contains disallowed functions or operators")
            
            # Evaluate the expression
            result = self._parse_and_evaluate(expression)
            
            # Return the result
            return result
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {str(e)}")