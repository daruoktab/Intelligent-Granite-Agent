import logging # Removed ast
import os
import json 
from datetime import datetime
from typing import Any, Dict, List, Callable # Removed Type

import ollama # Keep this for ollama.chat
from pydantic import BaseModel, ValidationError 
from config import DEFAULT_MODEL, LOG_FILE, LOG_LEVEL, ENABLED_TOOLS
# from ollama import chat # Removed redundant import
from tools.base import BaseTool
from tools.date_tools import DateCalculator, DateDifference, GetCurrentDate, GetCurrentTime, GetCurrentDayName
from tools.math_tools import ExpressionEvaluator
from tools.text_tools import TextAnalyzer, TextCounter, TextFormatter, SpecificLetterCounter # Added SpecificLetterCounter

logger = logging.getLogger(__name__)

class FormattedFinalResponse(BaseModel):
    natural_language_response: str

log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
logger.setLevel(log_level_map.get(LOG_LEVEL, logging.DEBUG))

for handler in logger.handlers[:]:
    logger.removeHandler(handler)

current_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_dir, LOG_FILE)
file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
file_handler.setLevel(log_level_map.get(LOG_LEVEL, logging.DEBUG))
formatter = logging.Formatter('## {asctime}\n**{levelname}**: {message}\n\n', style='{')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class Tools:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._all_possible_tools: Dict[str, Callable[[], BaseTool]] = {
            "evaluate_expression": ExpressionEvaluator,
            "calculate_date": DateCalculator,
            "date_difference": DateDifference,
            "get_current_date": GetCurrentDate,
            "get_current_time": GetCurrentTime,
            "get_current_day_name": GetCurrentDayName,
            "count_words": TextCounter,
            "analyze_text": TextAnalyzer,
            "format_text": TextFormatter,
            "count_specific_letter": SpecificLetterCounter, # Added new tool
        }
        self._register_default_tools()

    def _register_default_tools(self):
        for tool_name in ENABLED_TOOLS:
            tool_constructor = self._all_possible_tools.get(tool_name)
            if tool_constructor:
                self.register_tool(tool_constructor())
            else:
                logger.warning(f"Tool '{tool_name}' configured in ENABLED_TOOLS but not found in _all_possible_tools.")

    def register_tool(self, tool: BaseTool) -> None:
        self.tools[tool.name] = tool

    @property
    def tool_definitions(self) -> List[Dict]:
        return [tool.to_dict() for tool in self.tools.values()]

class ChatManager:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.tools = Tools()
        logger.info(f"ChatManager initialized with model: {model_name}")
        self.last_tool_usage_info: List[Dict[str, Any]] = []

    def _execute_tool_calls(self, tool_calls_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tool_results_for_llm: List[Dict[str, Any]] = []
        self.last_tool_usage_info = [] 

        for tool_call_item in tool_calls_data:
            function_details = tool_call_item.get('function', {})
            tool_name = function_details.get('name')
            # Arguments from LLM tool_calls are already parsed by ollama client if they are valid JSON strings
            # or directly passed as dicts. If it's a string, it needs parsing.
            raw_tool_args = function_details.get('arguments', {}) 
            call_id = tool_call_item.get('id', f"call_{tool_name}_{datetime.now().timestamp()}")

            logger.debug(f"Executing tool: {tool_name} with raw args: {raw_tool_args} (ID: {call_id})")
            
            args: Dict[str, Any] = {}
            if tool_name and tool_name in self.tools.tools:
                tool_instance = self.tools.tools[tool_name]
                try:
                    # The 'arguments' field from ollama.chat tool_calls should be a dict.
                    # If it's a string (e.g. from older versions or different models), parse it.
                    if isinstance(raw_tool_args, str):
                        args = json.loads(raw_tool_args)
                    elif isinstance(raw_tool_args, dict):
                        args = raw_tool_args
                    else:
                        raise ValueError("Tool arguments are not a valid JSON string or dictionary.")

                    if not isinstance(args, dict): # Should be redundant if above logic is correct
                        raise ValueError(f"Parsed tool arguments must be a dictionary, got {type(args)}")
                        
                    execution_result = tool_instance.execute(**args)
                    logger.debug(f"Tool {tool_name} execution result: {execution_result}")

                    tool_results_for_llm.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": tool_name, 
                        "content": str(execution_result), 
                    })
                    self.last_tool_usage_info.append({
                        "name": tool_name,
                        "description": tool_instance.description,
                        "arguments": args,
                        "result": execution_result
                    })
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
                    tool_results_for_llm.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": tool_name,
                        "content": f"Error executing tool {tool_name}: {str(e)}",
                    })
                    self.last_tool_usage_info.append({
                        "name": tool_name,
                        "description": tool_instance.description,
                        "arguments": args if args else raw_tool_args,
                        "result": f"Error: {str(e)}"
                    })
            else:
                logger.warning(f"Unknown or missing tool name called: {tool_name}")
                tool_results_for_llm.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": tool_name or "unknown_tool",
                    "content": f"Error: Unknown tool '{tool_name}' was called.",
                })
                self.last_tool_usage_info.append({
                        "name": tool_name or "unknown_tool",
                        "description": "Unknown tool",
                        "arguments": raw_tool_args,
                        "result": f"Error: Unknown tool '{tool_name}'"
                    })
        return tool_results_for_llm

    def _parse_llm_content(self, content_str: str) -> Any:
        content_to_parse = content_str.strip()
        if content_to_parse.startswith("```json"):
            content_to_parse = content_to_parse[len("```json"):].strip()
        if content_to_parse.startswith("```"):
            content_to_parse = content_to_parse[len("```"):].strip()
        if content_to_parse.endswith("```"):
            content_to_parse = content_to_parse[:-len("```")].strip()
        return json.loads(content_to_parse)

    def chat(self, prompt: str) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = []
        final_result_data: Dict[str, Any] = {
            "response": "An error occurred processing your request.",
            "tools_used": []
        }
        self.last_tool_usage_info = []

        try:
            system_prompt = """You are a highly intelligent assistant acting as a tool router and response synthesizer.
Your responses' `content` field MUST ALWAYS be a JSON string if you are not making tool calls.
If you decide to use tools, your response message should include a `tool_calls` array.

**Interaction Flow & Response Structure:**

1.  **Analyze User Query:** Determine if any available tools can help.

2.  **Your First Response (Assistant's Message):**
    *   **If tools are needed:** Your assistant message object should contain a `tool_calls` array (e.g., `{"role": "assistant", "tool_calls": [...]}`). The `content` field in this message can be null or a brief thought (e.g., `{"role": "assistant", "content": "Okay, using tools.", "tool_calls": [...]}`).
    *   **If NO tools are needed (e.g., direct answer, or asking for clarification):** Your assistant message object's `content` field MUST be a **JSON string** that successfully parses into `{"natural_language_response": "Your response here."}`. The `tool_calls` field must be absent or null.
        Example of the required JSON string for the `content` field: `"{\\"natural_language_response\\": \\"Your direct answer or clarification question.\\"}"`

3.  **Tool Execution (by the system):** If you requested tools, they will be executed.

4.  **Your Second Response (Synthesizing Tool Results):**
    *   After receiving tool results, your task is to synthesize them into a final answer.
    *   The `content` field of this second response message MUST ALSO be a **JSON string** that successfully parses into `{"natural_language_response": "Your synthesized answer."}`.
        Example of the required JSON string for the `content` field: `"{\\"natural_language_response\\": \\"Your synthesized answer based on tool results.\\"}"`

**`FormattedFinalResponse` Schema (this is what the JSON string in the `content` field must parse to when no tools are called, or when synthesizing tool results):**
```json
{{
  "natural_language_response": "string"
}}
```

**Key rules for the `natural_language_response` string (inside the JSON):**
-   MUST be plain natural language text.
-   NO JSON, XML, or other structured data *within* this string.
-   NO special tokens like `<|im_start|>`, `<|im_sep|>`.
-   DO NOT explicitly mention tool usage (e.g., "I used tool X...").
-   If a tool errored, acknowledge the difficulty if relevant, but provide a helpful natural language response (still within the JSON structure).
-   **Handling Text for Text Tools (`count_words`, `analyze_text`, `format_text`):**
    -   If the user provides explicit text within their prompt (e.g., "Count words in 'hello world'"), use that explicit text for the tool's `text` argument.
    -   If the user's prompt implies a text operation on the prompt itself (e.g., "Count the words in this sentence", "Analyze this query for sentiment"), then use the **full text of the user's current prompt** as the value for the `text` argument.
    -   If the text is clearly missing and cannot be inferred from the current prompt (e.g., user says "Count words" and nothing else), then and only then should you ask for clarification by responding with a `FormattedFinalResponse` JSON, e.g., `"{\\"natural_language_response\\": \\"What text would you like me to process?\\"}"`.

Here are the tools available to you:
- `calculate_date`: Calculates future or past dates.
  - To add time: `{"operation": "add", "amount": X, "unit": "days/months/years", "date": "YYYY-MM-DD or today"}`
  - To subtract time: `{"operation": "subtract", "amount": X, "unit": "days/months/years", "date": "YYYY-MM-DD or today"}`
- `date_difference`: Calculates days between two dates.
  - `{"date1": "YYYY-MM-DD or today", "date2": "YYYY-MM-DD or today"}`
- `get_current_date`: Gets the current date. (No arguments: `{}`)
- `get_current_time`: Gets the current time. (No arguments: `{}`)
- `get_current_day_name`: Gets the name of the current day. (No arguments: `{}`)
- `evaluate_expression`: Evaluates mathematical expressions.
  - `{"expression": "your_math_expression"}`
- `count_words`: Use this tool to count the number of words in a specific text provided by the user. The user MUST provide the text.
  - `{"text": "ACTUAL_TEXT_FROM_USER_PROMPT_OR_CONTEXT"}`
- `analyze_text`: Use this tool for a comprehensive analysis of a specific text provided by the user, including **character count (overall letter count)**, word count, sentence count, and average word length. The user MUST provide the text. This is preferred if the user asks for "total letter count" or "total character count".
  - `{"text": "ACTUAL_TEXT_FROM_USER_PROMPT_OR_CONTEXT"}`
- `format_text`: Formats a specific text provided by the user (uppercase, lowercase, titlecase, capitalize, strip). The user MUST provide the text.
  - `{"text": "ACTUAL_TEXT_FROM_USER_PROMPT_OR_CONTEXT", "operation": "operation_name"}`
- `count_specific_letter`: **You MUST use this tool** to count occurrences of a specific letter or substring within a given text if the user asks for it (e.g., "how many 'x' in 'text'"). The user MUST provide both the text and the letter/substring to count.
  - `{"text": "TEXT_TO_SEARCH_IN", "letter_to_count": "LETTER_OR_SUBSTRING"}`
"""
            messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})

            logger.debug(f"Initial chat call. Messages: {messages}")
            
            response_from_llm = ollama.chat(
                model=self.model_name,
                messages=messages,
                tools=self.tools.tool_definitions,
                format="json" 
            )
            
            assistant_message = response_from_llm['message'] 
            logger.debug(f"LLM first response (full message object): {assistant_message}")
            messages.append(assistant_message)

            llm_tool_calls = assistant_message.get('tool_calls')

            if llm_tool_calls:
                logger.info(f"LLM requested tool calls (from message.tool_calls): {llm_tool_calls}")
                
                tool_outputs = self._execute_tool_calls(llm_tool_calls) # Pass the list of dicts
                messages.extend(tool_outputs)
                
                logger.debug(f"Making follow-up chat call with tool results. Messages: {messages}")
                final_response_from_llm = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    format="json"
                )
                final_assistant_message_content_str = final_response_from_llm['message'].get('content', '{}')
                logger.debug(f"LLM final synthesized JSON response content string: {final_assistant_message_content_str}")

                try:
                    parsed_final_json = self._parse_llm_content(final_assistant_message_content_str)
                    validated_response = FormattedFinalResponse(**parsed_final_json)
                    final_result_data["response"] = validated_response.natural_language_response
                except (json.JSONDecodeError, ValidationError) as e:
                    logger.error(f"Error parsing/validating LLM's final synthesized JSON response: {e}. Raw content string: {final_assistant_message_content_str}")
                    final_result_data["response"] = "Error: Assistant's synthesized response was not in the expected format. Raw: " + final_assistant_message_content_str
            
            else: 
                logger.info("LLM did not request tools via message.tool_calls. Expecting FormattedFinalResponse in content.")
                assistant_content_str = assistant_message.get('content', '{}')
                
                try:
                    parsed_content_json = self._parse_llm_content(assistant_content_str)
                    # Check if the parsed content itself contains tool_calls (LLM might put it here)
                    if isinstance(parsed_content_json, dict) and 'tool_calls' in parsed_content_json and parsed_content_json['tool_calls']:
                        logger.info(f"LLM requested tool calls via content.tool_calls: {parsed_content_json['tool_calls']}")
                        tool_outputs = self._execute_tool_calls(parsed_content_json['tool_calls'])
                        messages.extend(tool_outputs)
                        
                        logger.debug(f"Making follow-up chat call with tool results from content.tool_calls. Messages: {messages}")
                        final_response_from_llm_alt = ollama.chat(
                            model=self.model_name,
                            messages=messages,
                            format="json"
                        )
                        final_assistant_message_content_str_alt = final_response_from_llm_alt['message'].get('content', '{}')
                        logger.debug(f"LLM final synthesized JSON (from content.tool_calls path): {final_assistant_message_content_str_alt}")
                        
                        try:
                            parsed_final_json_alt = self._parse_llm_content(final_assistant_message_content_str_alt)
                            validated_response_alt = FormattedFinalResponse(**parsed_final_json_alt)
                            final_result_data["response"] = validated_response_alt.natural_language_response
                        except (json.JSONDecodeError, ValidationError) as e_synth:
                            logger.error(f"Error parsing/validating LLM's final synthesized JSON (from content.tool_calls path): {e_synth}. Raw: {final_assistant_message_content_str_alt}")
                            final_result_data["response"] = "Error: Assistant's synthesized response was not in the expected format. Raw: " + final_assistant_message_content_str_alt
                    
                    elif isinstance(parsed_content_json, dict) and 'natural_language_response' in parsed_content_json:
                        logger.info("LLM provided FormattedFinalResponse directly in content.")
                        validated_response = FormattedFinalResponse(**parsed_content_json)
                        final_result_data["response"] = validated_response.natural_language_response
                    else:
                        logger.error(f"LLM's direct response content JSON is not FormattedFinalResponse or tool_calls. Content: {parsed_content_json}")
                        final_result_data["response"] = "Error: Assistant's direct response JSON structure was not recognized. Raw: " + assistant_content_str
                
                except (json.JSONDecodeError, ValidationError, TypeError) as e: 
                    logger.error(f"Error parsing/validating LLM's direct response from content: {e}. Raw content string: {assistant_content_str}")
                    final_result_data["response"] = "Error: Assistant's direct response was not in the expected format or structure. Raw: " + assistant_content_str
            
            final_result_data["tools_used"] = self.last_tool_usage_info
            return final_result_data

        except Exception as e:
            error_msg = f"Error during chat: {str(e)}"
            logger.error(error_msg, exc_info=True)
            final_result_data["response"] = error_msg
            final_result_data["tools_used"] = self.last_tool_usage_info
            return final_result_data

def main():
    try:
        chat_manager = ChatManager(DEFAULT_MODEL)
        logger.info("Starting chat application")
        
        print(f"Tool Calling System initialized with model: {DEFAULT_MODEL}")
        print("Available tools:")
        for tool_name in chat_manager.tools.tools.keys():
            print(f"- {tool_name}")
        print("\nType 'quit' to exit the application.")
        
        while True:
            prompt = input('\nEnter your prompt: ')
            if prompt.lower() in ['quit', 'exit', 'q']:
                break
                
            result = chat_manager.chat(prompt)
            
            print(f"\nResponse: {result['response']}")
            
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
