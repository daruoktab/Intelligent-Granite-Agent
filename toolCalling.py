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
            system_message = """You are a helpful assistant that determines if queries need tools.
            For the following types of questions, respond EXACTLY with:
            
            'date' for queries like:
            - "what date will it be X days/months/years from today"
            - "what date was X days/months/years ago"
            - "days between date1 and date2"
            
            'math' for queries like:
            - "what is 2 + 2"
            - "calculate 15% of 200"
            
            'text' for queries like:
            - "count the words in this text"
            - "analyze this paragraph"
            - "format this text to uppercase"
            
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
            return result in ['math', 'date', 'text']
        except Exception as e:
            logger.error(f"Error in should_use_tools: {e}")
            return False

    def get_explanation(self, prompt: str, tool_name: str, args: dict, result: Any) -> str:
        """Get a natural language explanation for the calculation result"""
        try:
            if tool_name == 'calculate_date':
                current_date = datetime.now().strftime('%Y-%m-%d')
                if args['operation'] == 'subtract':
                    return f"{args['amount']} {args['unit']} ago was {result}."
                else:
                    return f"{args['amount']} {args['unit']} from today will be {result}."
            elif tool_name == 'date_difference':
                return f"There are {result} days between {args['date1']} and {args['date2']}."
            elif tool_name == 'evaluate_expression':
                # For math expressions, just return the result
                return f"{result}"
            elif tool_name == 'count_words':
                return f"The text contains {result} words."
            elif tool_name == 'analyze_text':
                if isinstance(result, dict):
                    return f"The text contains {result.get('word_count', 0)} words, {result.get('character_count', 0)} characters, and approximately {result.get('sentence_count', 0)} sentences. The average word length is {result.get('average_word_length', 0)} characters."
                else:
                    return f"Text analysis complete: {result}"
            elif tool_name == 'format_text':
                return f"Here's the formatted text: {result}"
            else:
                # Generic response for any other tool
                return f"{result}"
        except Exception as e:
            logger.error(f"Error in get_explanation: {e}")
            return f"{result}"

    def process_response(self, response: ChatResponse, prompt: str) -> dict:
        """Process the response and handle tool calls
        
        Returns:
            dict: A dictionary containing the response text and tool usage information
        """
        result_data = {
            "response": "",
            "tools_used": []
        }
        
        if not response or not response.message:
            logger.debug("No response or message received")
            result_data["response"] = "No response received"
            return result_data
            
        message_content: str = str(response.message.content or "")
            
        if not hasattr(response.message, 'tool_calls') or not response.message.tool_calls:
            logger.debug("No tool calls in response")
            result_data["response"] = message_content if message_content else "No response received"
            return result_data

        try:
            results = []
            tool_args = []
            tool_names = []
            tool_usage_info = []
            
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
                        
                        # Create a tool usage record
                        tool_usage = {
                            "name": tool.function.name,
                            "description": tool_instance.description,
                            "arguments": args,
                            "result": result
                        }
                        tool_usage_info.append(tool_usage)
                        
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
                result_data["response"] = message_content if message_content else "No results generated"
                return result_data

            logger.debug(f"Final results: {results}")
            
            # Get a grounded response based on the tool results
            grounded_response = self.get_explanation(prompt, tool_names[0], tool_args[0], results[0])
            
            # Return both the response and tool usage information
            result_data["response"] = grounded_response
            result_data["tools_used"] = tool_usage_info
            
            return result_data
        except Exception as e:
            logger.error(f"Error in process_response: {e}", exc_info=True)
            result_data["response"] = message_content if message_content else f"Error: {str(e)}"
            return result_data

    def chat(self, prompt: str) -> dict:
        """Main chat function that handles the conversation
        
        Returns:
            dict: A dictionary containing the response and tool usage information
        """
        result = {
            "response": "",
            "tools_used": []
        }
        
        try:
            if self.should_use_tools(prompt):
                system_prompt = """You are a helpful assistant that provides clear, direct answers.
                When using tools, don't mention which tools you're using or how you're calculating the answer.
                Just provide the answer in a natural, conversational way.
                
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
                
                For text analysis, use the appropriate text tools.
                
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
                result["response"] = str(response.message.content or "No response received")
                return result
        except Exception as e:
            error_msg = f"Error during chat: {str(e)}"
            logger.error(error_msg)
            result["response"] = error_msg
            return result

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
            result = chat_manager.chat(prompt)
            
            # Display the response
            print(f"\nResponse: {result['response']}")
            
            # Display tool usage information if any tools were used
            if result.get('tools_used'):
                print("\nTools used:")
                for i, tool in enumerate(result['tools_used'], 1):
                    print(f"  {i}. {tool['name']}")
                    print(f"     Arguments: {tool['arguments']}")
                    print(f"     Result: {tool['result']}")
                    print()
            
        logger.info("Chat application terminated normally")
        print("\nThank you for using the Tool Calling System!")
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        print(f"An error occurred: {str(e)}")
        print("Check the log file for details.")

if __name__ == "__main__":
    main()

