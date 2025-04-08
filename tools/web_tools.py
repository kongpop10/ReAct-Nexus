"""
Web-related tools for the ReAct application.
Includes web search and web scraping functionality.
"""
import os
import json
import re
import requests
import streamlit as st
from tavily import TavilyClient
from data_acquisition.news_scraper import WebScraper
from data_acquisition.process_search_results import process_search_results
from utils.status import update_tool_status
from tools.firecrawl_tools import firecrawl_scrape

def extract_urls_from_markdown(markdown_text: str) -> list:
    """Extract all URLs from markdown-formatted text."""
    url_pattern = r'https?://[^\s\)\]\"]+'
    urls = re.findall(url_pattern, markdown_text)
    return urls

def detect_url_scrape_request(query: str) -> tuple:
    """Detect if a user is asking to scrape a URL for knowledge.

    Args:
        query (str): The user's query

    Returns:
        tuple: (is_scrape_request, url, memory_key, add_to_kb)
            - is_scrape_request (bool): True if the query is asking to scrape a URL
            - url (str): The URL to scrape, or None if no URL found
            - memory_key (str): Suggested memory key for storing the scraped content
            - add_to_kb (bool): True if the query is asking to add to knowledge base
    """
    # Common phrases that indicate a URL scrape request
    scrape_phrases = [
        "scrape", "extract", "get content", "get information",
        "use as knowledge", "use as reference", "use this url",
        "use this website", "use this link", "use this page",
        "read this website", "read this url", "read this link", "read this page"
    ]

    # Phrases that indicate adding to knowledge base
    kb_phrases = [
        "add to knowledge base", "save to knowledge base", "store in knowledge base",
        "remember for later", "save for future", "add to kb", "save to kb",
        "persist this", "keep this information", "save this information",
        "add to permanent memory", "save permanently"
    ]

    # Check if any scrape phrase is in the query (case insensitive)
    is_scrape_request = any(phrase.lower() in query.lower() for phrase in scrape_phrases)

    # Check if any knowledge base phrase is in the query
    add_to_kb = any(phrase.lower() in query.lower() for phrase in kb_phrases)

    # If explicitly asking to add to knowledge base, treat as a scrape request too
    if add_to_kb and not is_scrape_request:
        is_scrape_request = True

    # Extract URL from the query
    urls = extract_urls_from_markdown(query)
    url = urls[0] if urls else None

    # Generate a memory key based on the URL domain
    memory_key = None
    if url:
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Remove www. and .com/.org/etc. to create a clean key
            domain = domain.replace('www.', '')
            domain = domain.split('.')[0]  # Get the main domain name
            memory_key = f"scraped_{domain}"
        except:
            memory_key = "scraped_content"

    return (is_scrape_request, url, memory_key, add_to_kb)

def web_search(query: str) -> str:
    """
    Performs real web search using Tavily API and formats results in markdown.
    Requires TAVILY_API_KEY environment variable.
    """
    update_tool_status("web_search", query=query)

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return json.dumps({"error": "TAVILY_API_KEY not found in environment variables"})

    try:
        tavily = TavilyClient(api_key=api_key)
        search_result = tavily.search(query=query, max_results=3)
        results_json = json.dumps([
            {"title": result["title"], "url": result["url"], "snippet": result["content"]}
            for result in search_result["results"]
        ])

        # Format results in markdown
        return process_search_results(results_json)
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})

def is_document_url(url: str) -> bool:
    """Detect if a URL points to a document or binary file that requires special handling.

    Args:
        url (str): The URL to check

    Returns:
        bool: True if the URL appears to point to a document file, False otherwise
    """
    # List of file extensions that should be handled by Firecrawl
    document_extensions = [
        # PDF files
        '.pdf',
        # Microsoft Office documents
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        # OpenDocument formats
        '.odt', '.ods', '.odp',
        # Other document formats
        '.rtf', '.epub', '.mobi',
        # Archive formats
        '.zip', '.rar', '.7z', '.tar', '.gz',
        # Image formats (if they contain text that needs extraction)
        '.tiff', '.tif', '.png', '.jpg', '.jpeg',
        # Other binary formats
        '.csv', '.xml', '.json'
    ]

    # Check if the URL ends with any of the document extensions (case insensitive)
    url_lower = url.lower()
    if any(url_lower.endswith(ext) for ext in document_extensions):
        return True

    # Check if the URL contains document type indicators in the path
    document_indicators = [
        '/pdf/', '/pdfs/', '/doc/', '/docs/', '/document/', '/documents/',
        '/xls/', '/xlsx/', '/excel/', '/spreadsheet/', '/spreadsheets/',
        '/ppt/', '/pptx/', '/powerpoint/', '/presentation/', '/presentations/',
        '/download/', '/file/', '/attachment/', '/attachments/',
        'document.', 'file.', 'download.', 'attachment.'
    ]
    if any(indicator in url_lower for indicator in document_indicators):
        return True

    # Check if the URL has document-related query parameters
    document_params = [
        'format=pdf', 'type=pdf', 'download=pdf', 'file=pdf',
        'format=doc', 'type=doc', 'download=doc', 'file=doc',
        'format=xls', 'type=xls', 'download=xls', 'file=xls',
        'format=ppt', 'type=ppt', 'download=ppt', 'file=ppt',
        'format=docx', 'type=docx', 'download=docx', 'file=docx',
        'format=xlsx', 'type=xlsx', 'download=xlsx', 'file=xlsx',
        'format=pptx', 'type=pptx', 'download=pptx', 'file=pptx',
        'download=true', 'attachment=true', 'file=true', 'doc=true'
    ]
    if any(param in url_lower for param in document_params):
        return True

    return False

def web_scrape(url: str = None, urls: str = None) -> str:
    """Scrapes the text content of a given URL or list of URLs.

    For document files (PDF, Word, Excel, PowerPoint, etc.), automatically redirects to firecrawl_scrape
    for better document handling. For regular web pages, uses the WebScraper class.
    """
    # Handle both parameter names (url and urls) for backward compatibility
    target_url = url if url is not None else urls
    update_tool_status("web_scrape", url=target_url)

    if target_url is None:
        return "Error: No URL provided. Please provide a URL using the 'url' parameter."

    try:
        # Handle both single URL strings and lists of URLs
        if isinstance(target_url, str):
            # Check if the input might be a string representation of a list
            if target_url.startswith('[') and target_url.endswith(']'):
                try:
                    # Try to parse it as a JSON array
                    url_list = json.loads(target_url)
                    if isinstance(url_list, list):
                        results = {}
                        for single_url in url_list:
                            # Check if the URL is a document file
                            if is_document_url(single_url):
                                # Use firecrawl_scrape for document files
                                st.info(f"Detected document URL: {single_url}. Using Firecrawl for better document handling.")
                                firecrawl_result = json.loads(firecrawl_scrape(single_url))
                                if 'markdown' in firecrawl_result:
                                    results[single_url] = firecrawl_result['markdown']
                                else:
                                    results[single_url] = "PDF content could not be extracted. See full response: " + json.dumps(firecrawl_result)
                            else:
                                # Use regular scraper for non-PDFs
                                scraper = WebScraper()
                                results[single_url] = scraper.scrape_content(single_url)
                        return json.dumps(results)
                except json.JSONDecodeError:
                    # If it's not valid JSON, treat it as a single URL
                    single_url = target_url
                    # Check if the URL is a document file
                    if is_document_url(single_url):
                        # Use firecrawl_scrape for document files
                        st.info(f"Detected document URL: {single_url}. Using Firecrawl for better document handling.")
                        firecrawl_result = json.loads(firecrawl_scrape(single_url))
                        if 'markdown' in firecrawl_result:
                            return firecrawl_result['markdown']
                        else:
                            return "PDF content could not be extracted. See full response: " + json.dumps(firecrawl_result)
                    else:
                        # Use regular scraper for non-PDFs
                        scraper = WebScraper()
                        return scraper.scrape_content(single_url)
            else:
                # It's a regular URL string
                single_url = target_url
                # Check if the URL is a document file
                if is_document_url(single_url):
                    # Use firecrawl_scrape for document files
                    st.info(f"Detected document URL: {single_url}. Using Firecrawl for better document handling.")
                    firecrawl_result = json.loads(firecrawl_scrape(single_url))
                    if 'markdown' in firecrawl_result:
                        return firecrawl_result['markdown']
                    else:
                        return "PDF content could not be extracted. See full response: " + json.dumps(firecrawl_result)
                else:
                    # Use regular scraper for non-PDFs
                    scraper = WebScraper()
                    return scraper.scrape_content(single_url)
        elif isinstance(target_url, list):
            # It's already a list of URLs
            results = {}
            for single_url in target_url:
                # Check if the URL is a document file
                if is_document_url(single_url):
                    # Use firecrawl_scrape for document files
                    st.info(f"Detected document URL: {single_url}. Using Firecrawl for better document handling.")
                    firecrawl_result = json.loads(firecrawl_scrape(single_url))
                    if 'markdown' in firecrawl_result:
                        results[single_url] = firecrawl_result['markdown']
                    else:
                        results[single_url] = "PDF content could not be extracted. See full response: " + json.dumps(firecrawl_result)
                else:
                    # Use regular scraper for non-PDFs
                    scraper = WebScraper()
                    results[single_url] = scraper.scrape_content(single_url)
            return json.dumps(results)
        else:
            return f"Invalid URL format: {target_url}. Expected a string URL or a list of URLs."
    except Exception as e:
        return f"Failed to scrape {target_url}: {str(e)}"
