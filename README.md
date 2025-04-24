
# Tool Calling System

This repository contains a tool calling system that integrates various tools for date calculations, mathematical expression evaluations, and text processing into LLM (Large Language Model) based chatbots. The system provides both a command-line interface and a web interface.

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

- **Tool-based Architecture**: Modular design allows easy addition of new tools
- **Natural Language Interface**: Interact with tools using natural language
- **Web Interface**: User-friendly web UI for interacting with the system
- **Command Line Interface**: Traditional CLI for scripting and direct use
- **Transparent Tool Usage**: System shows which tools were used to answer questions
- **Logging**: Comprehensive logging of tool usage and results

## Tools

### Date Tools

- **DateCalculator**: Calculates dates by adding or subtracting days, months, or years from a given date.
- **DateDifference**: Calculates the difference in days between two dates.

### Math Tools

- **ExpressionEvaluator**: Evaluates mathematical expressions with support for various math functions.

### Text Tools

- **TextCounter**: Counts the number of words in a given text.
- **TextAnalyzer**: Analyzes text properties including character count, word count, sentence count, and average word length.
- **TextFormatter**: Formats text with operations like uppercase, lowercase, title case, etc.

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
   - For math calculations:
     - "What is 2 + 2?"
     - "Calculate 15% of 200"
     - "What is the square root of 144?"
   - For text processing:
     - "Count the words in this text."
     - "Analyze this paragraph for me."
     - "Convert this text to uppercase."

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
- python-dateutil

Install all dependencies with:
```
pip install -r requirements.txt
```