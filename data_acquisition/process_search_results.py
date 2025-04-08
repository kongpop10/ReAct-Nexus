import json
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

def process_search_results(json_str):
    """Process JSON search results and format them in markdown.

    Args:
        json_str (str): JSON string containing search results

    Returns:
        str: Formatted markdown string
    """
    try:
        # Parse JSON string to list
        results = json.loads(json_str)

        # Format each result in markdown
        markdown = ""
        for result in results:
            # Add title
            markdown += f"### {result['title']}\n\n"

            # Add URL as clickable link
            markdown += f"🔗 [{result['url']}]({result['url']})\n\n"

            # Process snippet to handle LaTeX and dollar amounts
            processed_snippet = escape_dollar_amounts(result['snippet'])

            # Add snippet with some formatting
            markdown += f"📝 {processed_snippet}\n\n"

            # Add separator between results
            markdown += "---\n\n"

        return markdown.strip()

    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {str(e)}"
    except Exception as e:
        return f"Error processing results: {str(e)}"

# Example usage
if __name__ == '__main__':
    # Sample JSON string
    sample_json = '''[
        {
            "title": "AI News | Latest AI News",
            "url": "https://example.com/ai-news",
            "snippet": "Latest AI news and updates..."
        }
    ]'''

    print(process_search_results(sample_json))