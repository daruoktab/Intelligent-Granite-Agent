
# Advanced Tool Integration with IBM Granite LLM: A Capstone Project

This capstone project showcases an advanced tool-calling system powered by an **IBM Granite series Large Language Model (LLM)**. It demonstrates the LLM's sophisticated capabilities in understanding user queries, intelligently selecting and invoking appropriate tools, and synthesizing information to provide accurate and context-aware responses. The system effectively extends the LLM's knowledge and functionalities by integrating external tools for tasks such as date calculations, mathematical evaluations, and text processing.

This repository provides both a command-line interface (CLI) and a user-friendly web interface to interact with this intelligent tool-integrated chatbot.

## Core Objective & Significance

The primary goal of this project is to explore and demonstrate the power of modern LLMs, specifically IBM Granite, in creating agentic systems that can:
-   Parse complex natural language prompts.
-   Reason about the necessary steps and tools required to fulfill a request.
-   Dynamically call external functions/tools with appropriate arguments.
-   Process tool outputs and generate coherent, natural language responses.

This work highlights a key advancement in AI – moving beyond simple text generation to creating systems that can act and interact with external data sources and services.

## Project Structure

```
├── toolCalling.py      # Main CLI application
├── web_app.py          # Web interface
├── config.py           # Configuration settings
├── requirements.txt    # Dependencies
├── log.md              # Log file
├── README.md           # Documentation
└── tools/              # Tool implementations
    ├── base.py         # Base tool class
    ├── date_tools.py   # Date calculation tools
    ├── math_tools.py   # Mathematical tools
    └── text_tools.py   # Text processing tools
```

## Features

- **Intelligent Tool Orchestration**: Powered by IBM Granite, the system intelligently determines when and how to use available tools based on user prompts.
- **Dynamic Function Calling**: Demonstrates the LLM's ability to format requests for external tools and parse their JSON responses.
- **Natural Language Understanding & Synthesis**: The LLM excels at interpreting diverse user inputs and generating human-like explanations from structured tool outputs.
- **Modular Toolset**: Easily extensible with new tools, each providing specific functionalities (date, math, text).
- **Dual Interfaces**: Accessible via a sleek, modern web UI (with dark mode) and a functional command-line interface.
- **Transparent Operation**: The web interface clearly shows which tools were invoked and their arguments/results, offering insight into the LLM's decision-making process.
- **Comprehensive Logging**: Detailed logs capture interactions, tool usage, and system behavior for analysis and debugging.

## Tools

### Date Tools

- **DateCalculator**: Calculates dates by adding or subtracting days, months, or years from a given date.
- **DateDifference**: Calculates the difference in days between two dates.
- **GetCurrentDate**: Retrieves the current date in YYYY-MM-DD format.
- **GetCurrentTime**: Retrieves the current time in HH:MM:SS format.
- **GetCurrentDayName**: Retrieves the name of the current day (e.g., Monday).

### Math Tools

- **ExpressionEvaluator**: Evaluates mathematical expressions with support for various math functions.

### Text Tools

- **TextCounter**: Counts the number of words in a given text.
- **TextAnalyzer**: Analyzes text properties including character count, word count, sentence count, and average word length.
- **TextFormatter**: Formats text with operations like uppercase, lowercase, title case, etc.
- **SpecificLetterCounter**: Counts the occurrences of a specific letter or substring within a given text (e.g., "how many 'a's in 'banana'").

## Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/yourusername/tool-calling-system.git
   cd tool-calling-system
   ```

2. **Install dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

### Command Line Interface

1. **Run the main script**:
   ```sh
   python toolCalling.py
   ```

2. **Enter your prompt**:
   - For date calculations:
     - "What date will it be X days/months/years from today?"
     - "What date was X days/months/years ago?"
     - "Days between date1 and date2"
     - "What is the current date?"
     - "What time is it?"
     - "What day of the week is it?"
   - For math calculations:
     - "What is 2 + 2?"
     - "Calculate 15% of 200"
     - "What is the square root of 144?"
   - For text processing:
     - "Count the words in this text."
     - "Analyze this paragraph for me."
     - "Convert this text to uppercase."
     - "How many times does 'the' appear in 'the quick brown fox jumps over the lazy dog'?"

3. **View the results**:
   The system will determine the appropriate tool to use, display the result, and show which tools were used.

### Web Interface

1. **Start the web server**:
   ```sh
   python web_app.py
   ```

2. **Open your browser**:
   Navigate to `http://localhost:12000` (or the port specified in your environment)

3. **Enter prompts and view results**:
   The web interface will show both the response and which tools were used to generate it.

## Configuration

Edit `config.py` to customize:
- Default LLM model
- Logging settings
- Enabled tools

## Logging

Logs are written to `log.md` in a markdown-friendly format. This includes tool arguments, execution results, and any errors encountered.

## Requirements

- Python 3.8+
- ollama library
- flask (for web interface)
- pydantic

Install all dependencies with:
```
pip install -r requirements.txt
```

## Visual Demonstration (Suggestion)

*(Consider adding a GIF or a short video here demonstrating the web interface in action, showcasing a user prompt, the tool selection process (if visible or logged), and the final synthesized response. This would significantly enhance the README.)*

## Capstone Project Significance

This project serves as a practical demonstration of leveraging advanced LLM capabilities for building intelligent, tool-augmented applications. The use of IBM Granite for sophisticated tool orchestration and natural language interaction highlights the potential for creating more powerful and versatile AI systems.
