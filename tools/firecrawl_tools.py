"""
Firecrawl tools for the ReAct application.
Includes advanced web scraping, crawling, and data extraction capabilities.
"""
import os
import json
import streamlit as st
from utils.status import update_tool_status

def firecrawl_scrape(url: str, formats: list = None, extract_schema: dict = None, extract_prompt: str = None, parse_pdf: bool = True) -> str:
    """
    Scrapes a URL using Firecrawl and returns the content in specified formats.

    Args:
        url (str): The URL to scrape
        formats (list, optional): List of formats to return. Options: ['markdown', 'html', 'json']. Defaults to ['markdown'].
        extract_schema (dict, optional): Schema for structured data extraction. Defaults to None.
        extract_prompt (str, optional): Prompt for extracting specific information without a schema. Defaults to None.
        parse_pdf (bool, optional): Whether to parse PDF content when the URL points to a PDF file. Defaults to True.

    Returns:
        str: JSON string containing the scraped content in the requested formats
    """
    update_tool_status("firecrawl_scrape", url=url, formats=formats, parse_pdf=parse_pdf)

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return json.dumps({"error": "FIRECRAWL_API_KEY not found in environment variables"})

    try:
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=api_key)

        # Set default formats if not provided
        if not formats:
            formats = ["markdown"]

        # Prepare parameters
        params = {
            "formats": formats,
            "parsePDF": parse_pdf
        }

        # Add JSON extraction options if provided
        if "json" in formats and (extract_schema or extract_prompt):
            params["jsonOptions"] = {}
            if extract_schema:
                params["jsonOptions"]["schema"] = extract_schema
            if extract_prompt:
                params["jsonOptions"]["prompt"] = extract_prompt

        # Scrape the URL
        result = app.scrape_url(url, params=params)

        # Format the response
        response = {
            "url": url,
            "formats_requested": formats,
        }

        # Add the scraped content based on requested formats
        for fmt in formats:
            if fmt in result:
                response[fmt] = result[fmt]

        # Add metadata if available
        if "metadata" in result:
            response["metadata"] = result["metadata"]

        return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Firecrawl scraping failed: {str(e)}"})

def firecrawl_crawl(url: str, limit: int = 10, formats: list = None, exclude_paths: list = None, parse_pdf: bool = True) -> str:
    """
    Crawls a website using Firecrawl and returns content from all crawled pages.

    Args:
        url (str): The starting URL to crawl
        limit (int, optional): Maximum number of pages to crawl. Defaults to 10.
        formats (list, optional): List of formats to return. Options: ['markdown', 'html']. Defaults to ['markdown'].
        exclude_paths (list, optional): List of paths to exclude from crawling. Defaults to None.
        parse_pdf (bool, optional): Whether to parse PDF content when URLs point to PDF files. Defaults to True.

    Returns:
        str: JSON string containing the crawl status and results
    """
    update_tool_status("firecrawl_crawl", url=url, limit=limit, formats=formats, parse_pdf=parse_pdf)

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return json.dumps({"error": "FIRECRAWL_API_KEY not found in environment variables"})

    try:
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=api_key)

        # Set default formats if not provided
        if not formats:
            formats = ["markdown"]

        # Prepare parameters
        params = {
            "limit": limit,
            "scrapeOptions": {
                "formats": formats,
                "parsePDF": parse_pdf
            }
        }

        # Add exclude paths if provided
        if exclude_paths:
            params["excludePaths"] = exclude_paths

        # Start the crawl and poll for results
        crawl_status = app.crawl_url(url, params=params, poll_interval=30)

        return json.dumps(crawl_status, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Firecrawl crawling failed: {str(e)}"})

def firecrawl_map(url: str, include_sitemap: bool = True, exclude_subdomains: bool = False) -> str:
    """
    Maps a website using Firecrawl and returns a list of all URLs.

    Args:
        url (str): The URL to map
        include_sitemap (bool, optional): Whether to use the sitemap for mapping. Defaults to True.
        exclude_subdomains (bool, optional): Whether to exclude subdomains. Defaults to False.

    Returns:
        str: JSON string containing the list of URLs
    """
    update_tool_status("firecrawl_map", url=url, include_sitemap=include_sitemap, exclude_subdomains=exclude_subdomains)

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return json.dumps({"error": "FIRECRAWL_API_KEY not found in environment variables"})

    try:
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=api_key)

        # Prepare parameters
        params = {
            "includeSitemap": include_sitemap,
            "excludeSubdomains": exclude_subdomains
        }

        # Map the website
        map_result = app.map_url(url, params=params)

        return json.dumps(map_result, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Firecrawl mapping failed: {str(e)}"})
