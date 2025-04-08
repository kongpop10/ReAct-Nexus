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

def format_results_to_markdown(results):
    """Convert search results to a readable markdown format.

    Args:
        results (list): List of dictionaries containing search results

    Returns:
        str: Formatted markdown string
    """
    markdown = ""

    for result in results:
        # Add title as heading
        markdown += f"## {result['title']}\n\n"

        # Add URL as link
        markdown += f"[Visit Article]({result['url']})\n\n"

        # Process snippet to handle LaTeX and dollar amounts
        processed_snippet = escape_dollar_amounts(result['snippet'])

        # Add snippet as regular text
        markdown += f"{processed_snippet}\n\n"

        # Add separator between articles
        markdown += "---\n\n"

    return markdown.strip()

def process_final_output(text):
    """
    Process the final output text to handle LaTeX and dollar amounts.

    Args:
        text (str): The final output text

    Returns:
        str: Processed text ready for display
    """
    return escape_dollar_amounts(text)