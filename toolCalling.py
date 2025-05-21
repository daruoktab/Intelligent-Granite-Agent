import logging
import os
import json 
from datetime import datetime
from typing import Any, Dict, List, Callable

import ollama
from pydantic import BaseModel, ValidationError 
from config import DEFAULT_MODEL, LOG_FILE, LOG_LEVEL, ENABLED_TOOLS
from tools.base import BaseTool
from tools.date_tools import DateCalculator, DateDifference, GetCurrentDate, GetCurrentTime, GetCurrentDayName
from tools.math_tools import ExpressionEvaluator
from tools.text_tools import TextAnalyzer, TextCounter, TextFormatter, SpecificLetterCounter

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
            "count_specific_letter": SpecificLetterCounter,
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
        
        for tool_call_item in tool_calls_data:
            function_details = tool_call_item.get('function', {})
            tool_name = function_details.get('name') 
            raw_tool_args = function_details.get('arguments', {}) 
            call_id = tool_call_item.get('id', f"call_{tool_name or 'invalid_tool_call'}_{datetime.now().timestamp()}")

            logger.debug(f"Attempting to execute tool: {tool_name} with raw args: {raw_tool_args} (ID: {call_id})")
            
            args: Dict[str, Any] = {}

            if not tool_name:
                logger.warning(f"LLM attempted to call a tool with no name (None or empty). Args: {raw_tool_args}. ID: {call_id}")
                tool_results_for_llm.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": "invalid_tool_request",
                    "content": "Error: Tool name was missing or invalid in the request.",
                })
                self.last_tool_usage_info.append({
                    "name": "invalid_tool_request",
                    "description": "Attempt to call a tool with no name.",
                    "arguments": raw_tool_args,
                    "result": "Error: Tool name was missing or invalid."
                })
                continue

            if tool_name in self.tools.tools:
                tool_instance = self.tools.tools[tool_name]
                try:
                    if isinstance(raw_tool_args, str):
                        args = json.loads(raw_tool_args)
                    elif isinstance(raw_tool_args, dict):
                        args = raw_tool_args
                    else:
                        raise ValueError("Tool arguments are not a valid JSON string or dictionary.")

                    if not isinstance(args, dict):
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
                logger.warning(f"Unknown tool name called: {tool_name}")
                tool_results_for_llm.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": tool_name, 
                    "content": f"Error: Unknown tool '{tool_name}' was called.",
                })
                self.last_tool_usage_info.append({
                        "name": tool_name,
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
Your responses should follow these rules:

**Interaction Flow & Response Structure:**

1.  **Analyze User Query:** Determine if any available tools can help.

2.  **Your First Response (Assistant's Message):**
    *   **If tools are needed:** Your assistant message object MUST have a `tool_calls` array at the top level. The `name` field within each tool call object MUST be a valid, non-empty string from the list of available tools. The `content` field can be null or a brief thought.
        Example CORRECT structure: `{"role": "assistant", "tool_calls": [{"name": "tool_name", "arguments": {"arg1": "value1"}}], "content": "Thinking..."}`
        **CRITICAL:** DO NOT put the `tool_calls` array inside the `content` field.
        Example INCORRECT structure: `{"role": "assistant", "content": "{\\"tool_calls\\": [...]}"}`
        **CRITICAL:** You MUST provide a valid, non-empty string for the `name` field in each tool call object. Do not use `null` or an empty string for the tool name.
    *   **If NO tools are needed (e.g., direct answer, or asking for clarification):** Your assistant message object's `content` field MUST be a **plain natural language string**. The `tool_calls` field must be absent or null. DO NOT include any special tokens like `<|tool_call|>` in your direct answer content.
        Example: `{"role": "assistant", "content": "Your direct answer or clarification question."}`

**Iterative Tool Use & Multi-Step Tasks:**
- If a query requires multiple steps, you MUST request tools **strictly one at a time**.
- Your `tool_calls` array should contain **ONLY ONE** tool call object for the immediate next logical step.
- Use the concrete results from a previous tool call as arguments for the next tool call.

- **MANDATORY AND EXCLUSIVE RULE for 'date difference with today':**
  If the user asks for a date difference involving 'today' (e.g., "days between today and YYYY-MM-DD" or "how many days from today until YYYY-MM-DD"):
  1.  **Your First Turn Response MUST BE:** `{"role": "assistant", "tool_calls": [{"name": "get_current_date", "arguments": {}}]}`. No other tools.
  2.  (System executes `get_current_date` and returns the actual current date string, e.g., "2025-05-21").
  3.  **Your Second Turn Response MUST BE:** `{"role": "assistant", "tool_calls": [{"name": "date_difference", "arguments": {"date1": "YYYY-MM-DD_FROM_GET_CURRENT_DATE_RESULT", "date2": "YYYY-MM-DD_FROM_USER_PROMPT"}}]}`. Use the actual date string from step 2 for `date1`. No other tools.
  4.  (System executes `date_difference`).
  5.  **Your Third Turn Response MUST BE the final answer:** `{"role": "assistant", "content": "{\\"natural_language_response\\": \\"The difference is X days.\\"}"}`.
  **YOU ARE FORBIDDEN FROM USING THE `calculate_date` TOOL AT ANY POINT FOR THIS SPECIFIC 'date difference with today' SCENARIO. ONLY `get_current_date` THEN `date_difference` IS ALLOWED.**

- **General Multi-Step Example (e.g., "What is the weather like on the date 3 days after today?"):**
  1. Your first response: `{"role": "assistant", "tool_calls": [{"name": "get_current_date", "arguments": {}}]}`
  2. System executes, returns (e.g.) `{"role": "tool", "name": "get_current_date", "content": "2025-05-21"}`.
  3. Your second response: `{"role": "assistant", "tool_calls": [{"name": "calculate_date", "arguments": {"date": "2025-05-21", "operation": "add", "amount": 3, "unit": "days"}}]}`
  4. System executes, returns (e.g.) `{"role": "tool", "name": "calculate_date", "content": "2025-05-24"}`.
  5. Your third response: (Assuming a hypothetical `get_weather` tool) `{"role": "assistant", "tool_calls": [{"name": "get_weather", "arguments": {"date": "2025-05-24"}}]}`
  6. System executes, returns weather.
  7. Your fourth response (final answer): `{"role": "assistant", "content": "{\\"natural_language_response\\": \\"The weather on 2025-05-24 is sunny.\\"}"}`.
- **CRITICAL:** For any date calculations involving 'today', ALWAYS call `get_current_date` first. Then use the returned date string (e.g., "2025-05-21") as an argument in subsequent calls to `date_difference` or `calculate_date`. Do NOT use placeholders like `"{current_date}"`.
- If you lack information for a tool's arguments, ask the user for clarification instead of guessing or using placeholders.

3.  **Tool Execution (by the system):** If you requested a tool, it will be executed.

4.  **Your Response After Tool Execution (or if no tools were needed initially):**
    *   If more tool calls are needed to complete the task (iterative process), provide a new `tool_calls` array (containing ONLY ONE tool call).
    *   If the task is complete OR if no tools were called in the first place:
        *   **Case A: Direct Answer (No tools were ever called for this user prompt):** Your `content` field MUST be a **plain natural language string**. DO NOT include any special tokens like `<|tool_call|>`.
            Example: `{"role": "assistant", "content": "This is a direct answer."}`
        *   **Case B: Synthesized Final Answer (Tools were called and executed, and now you are providing the final result):**
            **CRITICAL REQUIREMENT:** Your `content` field MUST be a **JSON string** that successfully parses into the `FormattedFinalResponse` schema: `{"natural_language_response": "Your synthesized answer based on tool results."}`.
            Example of the required JSON string for the `content` field: `"{\\"natural_language_response\\": \\"The result of formatting 'ALL CAPS' to lowercase is 'all caps'.\\"}"`
            DO NOT simply return plain text if tools were used; you MUST use this JSON structure for the final synthesized response.

**`FormattedFinalResponse` Schema (ONLY for synthesized final answers AFTER tool execution):**
```json
{{
  "natural_language_response": "string"
}}
```

**Key rules for the `natural_language_response` string (inside the JSON, for synthesized results):**
-   MUST be plain natural language text.
-   NO JSON, XML, or other structured data *within* this string.
-   NO special tokens like `<|im_start|>`, `<|im_sep|>`.
-   DO NOT explicitly mention tool usage (e.g., "I used tool X...").
-   If a tool errored, acknowledge the difficulty if relevant, but provide a helpful natural language response (still within the JSON structure).
-   **Handling Text for Text Tools (`count_words`, `analyze_text`, `format_text`):**
    -   If the user provides explicit text within their prompt (e.g., "Count words in 'hello world'"), use that explicit text for the tool's `text` argument.
    -   If the user's prompt implies a text operation on the prompt itself (e.g., "Count the words in this sentence", "Analyze this query for sentiment"), then use the **full text of the user's current prompt** as the value for the `text` argument.
    -   If the text is clearly missing and cannot be inferred from the current prompt (e.g., user says "Count words" and nothing else), then and only then should you ask for clarification by responding with a plain natural language string, e.g., `"What text would you like me to process?"`.

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
  - **IMPORTANT for `evaluate_expression`**:
    - Always use `**` for exponentiation (e.g., `2**3` for 2 to the power of 3). Do NOT use `^`.
    - Pay close attention to order of operations. Use parentheses `()` to ensure correct sequencing, especially with the word "then".
    - "Then" means the operation(s) *before* "then" must be fully resolved (as if in parentheses) before the operation *after* "then" is applied to that result.
    - Example 1: "What is 5 plus 3, then multiplied by 2?" should be `(5 + 3) * 2`.
    - Example 2: "What is 9 times 14, then power by 2?" should be `(9 * 14)**2`.
    - Example 3 (Multiple "then"s): "What is 2 plus 3, then times 4, then minus 1, then power by 2?" should be `((((2 + 3) * 4) - 1)**2)`. Each "then" groups the preceding result.
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
            
            MAX_ITERATIONS = 5
            for i in range(MAX_ITERATIONS):
                logger.debug(f"Tool calling iteration {i+1}/{MAX_ITERATIONS}")
                
                response_from_llm = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    tools=self.tools.tool_definitions
                )
                
                assistant_message = response_from_llm['message']
                messages.append(assistant_message)
                logger.debug(f"LLM response (iteration {i+1}): {assistant_message}")

                llm_tool_calls = assistant_message.get('tool_calls')
                assistant_content_str = assistant_message.get('content', '')

                if not llm_tool_calls and assistant_content_str:
                    try:
                        parsed_content_for_tools = self._parse_llm_content(assistant_content_str)
                        if isinstance(parsed_content_for_tools, dict) and parsed_content_for_tools.get('tool_calls'):
                            llm_tool_calls = parsed_content_for_tools['tool_calls']
                            logger.info(f"Found tool_calls within content field (iteration {i+1}): {llm_tool_calls}")
                    except json.JSONDecodeError:
                        logger.debug("Content was not JSON or did not contain tool_calls when checking for nested tool_calls.")
                    except Exception as e_parse_content:
                        logger.error(f"Unexpected error parsing content for tool_calls: {e_parse_content}")

                if llm_tool_calls:
                    logger.info(f"LLM requested tool calls (iteration {i+1}): {llm_tool_calls}")
                    tool_outputs = self._execute_tool_calls(llm_tool_calls)
                    messages.extend(tool_outputs)

                    if i == MAX_ITERATIONS - 1:
                        logger.warning("Max tool iterations reached, but LLM still requesting tools. Attempting to get a final summary.")
                        summary_messages = messages + [{"role": "user", "content": "Please summarize the current state or provide a final answer based on the information gathered so far, without using any more tools."}]
                        final_summary_response = ollama.chat(model=self.model_name, messages=summary_messages)
                        final_result_data["response"] = final_summary_response['message'].get('content', "Max iterations reached. Could not complete.")
                        break
                else: 
                    logger.info(f"LLM did not request tools (iteration {i+1}). Expecting final answer.")
                    
                    is_first_pass_direct_answer = (i == 0 and not self.last_tool_usage_info)
                    
                    # Clean potential <|tool_call|> prefix from content string
                    cleaned_assistant_content_str = assistant_content_str.removeprefix("<|tool_call|>").strip()

                    if is_first_pass_direct_answer:
                        logger.info("Handling as direct plain text response (first pass, no tools).")
                        try:
                            parsed_json_content = self._parse_llm_content(cleaned_assistant_content_str)
                            if isinstance(parsed_json_content, dict) and 'role' in parsed_json_content and 'content' in parsed_json_content:
                                logger.info("Direct response was a nested JSON message. Extracting inner content.")
                                final_result_data["response"] = parsed_json_content.get('content', cleaned_assistant_content_str)
                            else:
                                logger.warning(f"Direct response was JSON but not the expected nested message structure: {cleaned_assistant_content_str}")
                                final_result_data["response"] = cleaned_assistant_content_str
                        except json.JSONDecodeError:
                            logger.info("Direct response is plain text as expected.")
                            final_result_data["response"] = cleaned_assistant_content_str
                    else:
                        logger.info("Handling as synthesized response (expected FormattedFinalResponse JSON).")
                        try:
                            parsed_final_json = self._parse_llm_content(cleaned_assistant_content_str)
                            validated_response = FormattedFinalResponse(**parsed_final_json)
                            final_result_data["response"] = validated_response.natural_language_response
                        except json.JSONDecodeError:
                            logger.warning(f"Synthesized response was not valid JSON. Content: '{cleaned_assistant_content_str}'. Treating as plain text.")
                            final_result_data["response"] = cleaned_assistant_content_str
                        except ValidationError as e_val:
                            logger.error(f"Error validating FormattedFinalResponse: {e_val}. Raw: '{cleaned_assistant_content_str}'")
                            extracted_error_message = "Error: Assistant's synthesized response was not in the expected FormattedFinalResponse structure."
                            try:
                                error_json = self._parse_llm_content(cleaned_assistant_content_str)
                                if isinstance(error_json, dict):
                                    if "data" in error_json and isinstance(error_json["data"], dict) and "message" in error_json["data"] and isinstance(error_json["data"]["message"], str):
                                        extracted_error_message = error_json["data"]["message"]
                                        logger.warning(f"Extracted error message from LLM's non-standard JSON (data.message): {extracted_error_message}")
                                    elif "error" in error_json and isinstance(error_json["error"], str):
                                        extracted_error_message = error_json["error"]
                                        logger.warning(f"Extracted error message from LLM's non-standard JSON (error): {extracted_error_message}")
                                    elif "message" in error_json and isinstance(error_json["message"], str):
                                        extracted_error_message = error_json["message"]
                                        logger.warning(f"Extracted message from LLM's non-standard JSON (message): {extracted_error_message}")
                                final_result_data["response"] = extracted_error_message 
                            except json.JSONDecodeError:
                                final_result_data["response"] = extracted_error_message + " Raw (not valid JSON): " + cleaned_assistant_content_str
                        except Exception as e_gen:
                             logger.error(f"Unexpected error processing synthesized response: {e_gen}. Raw: '{cleaned_assistant_content_str}'")
                             final_result_data["response"] = "Error processing assistant's final response. Raw: " + cleaned_assistant_content_str
                    break 
            else: 
                if not final_result_data.get("response") or final_result_data["response"] == "An error occurred processing your request.":
                    logger.error("Max tool iterations reached, and no final response was formulated by the LLM.")
                    final_result_data["response"] = "Max tool iterations reached. The assistant could not complete the request without a final answer."

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
            
            if not prompt.strip():
                print("No input received. Please type a prompt or 'quit' to exit.")
                continue
                
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
