"""Configuration settings for the tool calling system."""

# Model configuration
DEFAULT_MODEL = "llama3.2"
FALLBACK_MODEL = "llama2"

# Logging configuration
LOG_FILE = "log.md"
LOG_LEVEL = "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Tool configuration
ENABLED_TOOLS = ["evaluate_expression", "calculate_date", "date_difference", "count_words"]