from typing import Any, Dict # Removed Callable

class BaseTool:
    name: str
    description: str
    parameters: Dict[str, Any]

    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters

    def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError("Tool must implement execute method")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': self.parameters,
            }
        }
