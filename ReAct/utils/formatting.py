"""
Text formatting utilities for the ReAct application.
"""
import re

def escape_dollar_amounts(text):
    """
    Escape dollar amounts in text to prevent confusion with LaTeX delimiters.

    Args:
        text (str): The input text that may contain dollar amounts

    Returns:
        str: Text with dollar amounts properly escaped
    """
    # Pattern to match dollar amounts: $ followed by digits
    # This regex looks for $ followed by digits, with optional commas and decimal point
    dollar_pattern = r'(\$)(\d{1,3}(,\d{3})*(\.[0-9]+)?|\d+(\.[0-9]+)?)'

    # Replace with escaped dollar sign for Markdown
    escaped_text = re.sub(dollar_pattern, r'\\\1\2', text)

    return escaped_text
