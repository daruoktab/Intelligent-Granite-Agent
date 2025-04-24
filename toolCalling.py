import ollama
from ollama import chat, ChatResponse
import ast
from typing import Dict, List, Type, Any
import logging
from tools.base import BaseTool
from tools.math_tools import ExpressionEvaluator
from tools.date_tools import DateCalculator, DateDifference
from tools.text_tools import TextCounter, TextAnalyzer, TextFormatter
from datetime import datetime
import os
from config import DEFAULT_MODEL, LOG_FILE, LOG_LEVEL

# Configure logging to write to markdown file
logger = logging.getLogger(__name__)

# Set log level from config
log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
logger.setLevel(log_level_map.get(LOG_LEVEL, logging.DEBUG))

# Remove any existing handlers (to prevent console output)
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create markdown file handler with absolute path
current_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_dir, LOG_FILE)

# Create markdown file handler
file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
file_handler.setLevel(log_level_map.get(LOG_LEVEL, logging.DEBUG))

# Create markdown-friendly formatter
formatter = logging.Formatter('## {asctime}\n**{levelname}**: {message}\n\n', style='{')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class Tools:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        self.register_tool(ExpressionEvaluator())
        self.register_tool(DateCalculator())
        self.register_tool(DateDifference())
        self.register_tool(TextCounter())
        self.register_tool(TextAnalyzer())
        self.register_tool(TextFormatter())

    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool"""
        self.tools[tool.name] = tool

    @property
    def tool_definitions(self) -> List[Dict]:
        """Get all tool definitions"""
        return [tool.to_dict() for tool in self.tools.values()]

class ChatManager:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.tools = Tools()
        logger.info(f"ChatManager initialized with model: {model_name}")

    def should_use_tools(self, prompt: str) -> bool:
        """Determine if the prompt requires tool usage"""
        try:
            system_message = """You are a helpful assistant that determines if queries need calculations.
            For the following types of questions, respond EXACTLY with:
            
            'date' for queries like:
            - "what date will it be X days/months/years from today"
            - "what date was X days/months/years ago"
            - "days between date1 and date2"
            
            'math' for queries like:
            - "what is 2 + 2"
            - "calculate 15% of 200"
            
            'none' for all other queries.
            
            Respond with ONLY ONE WORD from the above options."""
            
            response = chat(
                self.model_name,
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': prompt}
                ]
            )
            result = response.message.content.lower() if response and response.message and response.message.content else 'none'
            logger.debug(f"Tool detection result: {result}")
            return result in ['math', 'date']
        except Exception as e:
            logger.error(f"Error in should_use_tools: {e}")
            return False

    def get_explanation(self, prompt: str, tool_name: str, args: dict, result: Any) -> str:
        """Get LLM explanation for the calculation result"""
        try:
            if tool_name == 'calculate_date':
                current_date = datetime.now().strftime('%Y-%m-%d')
                if args['operation'] == 'subtract':
                    return f"According to the calculation, {args['amount']} {args['unit']} ago from {current_date} was {result}."
                else:
                    return f"According to the calculation, {args['amount']} {args['unit']} from {current_date} will be {result}."
            elif tool_name == 'date_difference':
                return f"The exact number of days between {args['date1']} and {args['date2']} is {result} days."
            elif tool_name == 'evaluate_expression':
                return f"The result of the calculation is {result}."
            else:
                return f"The result is {result}"
        except Exception:
            return f"The calculation resulted in: {result}"

    def process_response(self, response: ChatResponse, prompt: str) -> str:
        """Process the response and handle tool calls"""
        if not response or not response.message:
            logger.debug("No response or message received")
            return "No response received"
            
        message_content: str = str(response.message.content or "")
            
        if not hasattr(response.message, 'tool_calls') or not response.message.tool_calls:
            logger.debug("No tool calls in response")
            return message_content if message_content else "No response received"

        try:
            results = []
            tool_args = []
            tool_names = []
            
            logger.debug(f"Processing tool calls: {response.message.tool_calls}")
            
            for tool in response.message.tool_calls:
                logger.debug(f"Processing tool: {tool.function.name}")
                if tool.function.name in self.tools.tools:
                    tool_instance = self.tools.tools[tool.function.name]
                    try:
                        args_str = tool.function.arguments
                        if isinstance(args_str, str):
                            args = ast.literal_eval(args_str)
                        else:
                            args = args_str
                            
                        logger.debug(f"Tool arguments: {args}")
                        
                        if not isinstance(args, dict):
                            raise ValueError(f"Tool arguments must be a dictionary, got {type(args)}")
                            
                        result = tool_instance.execute(**args)
                        logger.debug(f"Tool execution result: {result}")
                        
                        results.append(result)
                        tool_args.append(args)
                        tool_names.append(tool.function.name)
                    except (ValueError, SyntaxError) as e:
                        logger.error(f"Error executing tool: {e}")
                        continue
                else:
                    logger.warning(f"Unknown tool: {tool.function.name}")

            if not results:
                logger.warning("No successful tool executions")
                return message_content if message_content else "No results generated"

            logger.debug(f"Final results: {results}")
            # Get LLM explanation using the calculation result
            return self.get_explanation(prompt, tool_names[0], tool_args[0], results[0])
        except Exception as e:
            logger.error(f"Error in process_response: {e}", exc_info=True)
            return message_content if message_content else f"Error: {str(e)}"

    def chat(self, prompt: str) -> str:
        """Main chat function that handles the conversation"""
        try:
            if self.should_use_tools(prompt):
                system_prompt = """You are a helpful assistant with access to calculation tools.
                For date calculations, follow these EXACT formats:
                
                1. For future dates (X days/months/years from today):
                   Use calculate_date with:
                   {"operation": "add", "amount": X, "unit": "days", "date": "today"}
                
                2. For past dates (X days/months/years ago):
                   Use calculate_date with:
                   {"operation": "subtract", "amount": X, "unit": "days", "date": "today"}
                
                3. For date differences:
                   Use date_difference with:
                   {"date1": "YYYY-MM-DD", "date2": "YYYY-MM-DD"}
                
                Always use these exact formats and don't modify them."""
                
                logger.debug(f"Sending prompt with tools: {prompt}")
                response = chat(
                    self.model_name,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt}
                    ],
                    tools=self.tools.tool_definitions
                )
                logger.debug(f"Tool response: {response.message}")
                return self.process_response(response, prompt)
            else:
                response = chat(
                    self.model_name,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return str(response.message.content or "No response received")
        except Exception as e:
            return f"Error during chat: {str(e)}"

def main():
    """Main function to run the chat application."""
    try:
        # Initialize the chat manager with the default model
        chat_manager = ChatManager(DEFAULT_MODEL)
        logger.info("Starting chat application")
        
        print(f"Tool Calling System initialized with model: {DEFAULT_MODEL}")
        print("Available tools:")
        for tool_name in chat_manager.tools.tools.keys():
            print(f"- {tool_name}")
        print("\nType 'quit' to exit the application.")
        
        # Main chat loop
        while True:
            prompt = input('\nEnter your prompt: ')
            if prompt.lower() in ['quit', 'exit', 'q']:
                break
                
            # Process the prompt and get a response
            response = chat_manager.chat(prompt)
            print(f"\nResponse: {response}")
            
        logger.info("Chat application terminated normally")
        print("\nThank you for using the Tool Calling System!")
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        print(f"An error occurred: {str(e)}")
        print("Check the log file for details.")

if __name__ == "__main__":
    main()

