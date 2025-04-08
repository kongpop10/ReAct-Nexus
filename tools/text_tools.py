"""
Text processing tools for the ReAct application.
Includes URL extraction and other text manipulation functions.
"""
import re
from utils.status import update_tool_status

def text_extract_urls(text: str) -> str:
    """
    Extracts all URLs from the provided text.
    
    Args:
        text (str): The text to extract URLs from
        
    Returns:
        str: A JSON-formatted list of extracted URLs
    """
    update_tool_status("text_extract_urls", text=text[:100] + "..." if len(text) > 100 else text)
    
    # Regular expression for URL extraction
    url_pattern = r'https?://[^\s\)\]\"\'\<\>]+'
    
    # Find all URLs in the text
    urls = re.findall(url_pattern, text)
    
    if not urls:
        return "No URLs found in the provided text."
    
    # Format the result
    result = "Extracted URLs:\n\n"
    for i, url in enumerate(urls, 1):
        result += f"{i}. {url}\n"
    
    return result
