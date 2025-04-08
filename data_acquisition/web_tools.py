"""Provides web search and scraping functionalities."""

import os
import json
import streamlit as st

def web_search(query: str) -> str:
    """
    Performs real web search using Tavily API and formats results in markdown.
    Requires TAVILY_API_KEY environment variable.
    """
    st.write(f"TOOL: web_search(query='{query}')")

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return json.dumps({"error": "TAVILY_API_KEY not found in environment variables"})

    try:
        from agent_workspace.process_search_results import process_search_results

        tavily = TavilyClient(api_key=api_key)
        search_result = tavily.search(query=query, max_results=3)
        results_json = json.dumps([
            {"title": result["title"], "url": result["url"], "snippet": result["content"]}
            for result in search_result["results"]
        ])

        return process_search_results(results_json)
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})

def web_scrape(url: str = None, urls: str = None) -> str:
    """Scrapes the text content of a given URL or list of URLs using WebScraper class."""
    target_url = url if url is not None else urls
    st.write(f"TOOL: web_scrape(url='{target_url}')")

    if target_url is None:
        return "Error: No URL provided. Please provide a URL using the 'url' parameter."

    from agent_workspace.news_scraper import WebScraper

    try:
        scraper = WebScraper()

        if isinstance(target_url, str):
            if target_url.startswith('[') and target_url.endswith(']'):
                try:
                    url_list = json.loads(target_url)
                    if isinstance(url_list, list):
                        results = {}
                        for single_url in url_list:
                            results[single_url] = scraper.scrape_content(single_url)
                        return json.dumps(results)
                except json.JSONDecodeError:
                    return scraper.scrape_content(target_url)
            else:
                return scraper.scrape_content(target_url)
        elif isinstance(target_url, list):
            results = {}
            for single_url in target_url:
                results[single_url] = scraper.scrape_content(single_url)
            return json.dumps(results)
        else:
            return f"Invalid URL format: {target_url}. Expected a string URL or a list of URLs."
    except Exception as e:
        return f"Failed to scrape {target_url}: {str(e)}"