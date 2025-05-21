"""Configuration settings for the tool calling system."""

# Model configuration
DEFAULT_MODEL = "granite3.3"

# Logging configuration
LOG_FILE = "log.md"
LOG_LEVEL = "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Tool configuration
ENABLED_TOOLS = [
    "evaluate_expression", 
    "calculate_date", 
    "date_difference", 
    "get_current_date",
    "get_current_time",
    "get_current_day_name",
    "count_words",
    "analyze_text",
    "format_text",
    "count_specific_letter"
]
