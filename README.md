
# Tool Calling System

This repository contains a tool calling system that integrates various tools for date calculations, mathematical expression evaluations, and text processing. The system uses a chat-based interface to determine the appropriate tool to use based on user prompts.

## Project Structure

```

├── log.md
├── README.md
└── tools
    ├── base.py
    ├── date_tools.py
    ├── math_tools.py
    └── text_tools.py
```
## Tools

### Date Tools

- **DateCalculator**: Calculates dates by adding or subtracting days, months, or years from a given date.
- **DateDifference**: Calculates the difference in days between two dates.

### Math Tools

- **ExpressionEvaluator**: Evaluates mathematical expressions.

### Text Tools

- **TextCounter**: Counts the number of words in a given text.

## Usage

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
   - For text processing:
     - "Count the words in this text."

3. **View the results**:
   The system will determine the appropriate tool to use and display the result.

## Logging

Logs are written to `log.md` in a markdown-friendly format. This includes tool arguments, execution results, and any errors encountered.

## Requirement

ollama library
```
pip install ollama
```