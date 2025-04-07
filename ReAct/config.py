"""
Configuration settings and constants for the ReAct application.
"""
import os
import json
import threading
from datetime import datetime

# --- Constants ---
WORKSPACE_DIR = "agent_workspace"
MODEL_CONFIG_FILE = "model_config.json"

# --- Default Models ---
DEFAULT_MODELS = {
    "planner_model": "google/gemini-2.0-flash-thinking-exp:free",
    "executor_model": "google/gemini-2.0-flash-exp:free",
    "summarizer_model": "google/gemini-2.0-flash-thinking-exp:free",
    "title_model": "google/gemini-2.0-flash-exp:free"
}

# --- Tool Descriptions ---
TOOL_DESCRIPTIONS = """
Available Tools:
- web_search(query: str): Searches the web for the given query. Returns a list of search results (title, url, snippet).
- web_scrape(url: str): Fetches and extracts the main text content from a given URL or list of URLs. Returns the text content or a JSON object with URLs as keys and content as values. You can also directly ask to scrape a URL and use it as knowledge in the conversation (e.g., "Please scrape https://example.com and use it as knowledge").
- get_stock_data(symbol: str) or get_stock_data(ticker: str) or get_stock_data(stock_symbol: str): Fetches real-time stock data for the given stock symbol using Alpha Vantage API. Returns stock information in JSON format.
- read_file(filename: str): Reads the content of the specified file from the workspace. Returns the file content.
- write_file(filename: str, content: str, append: bool = False) or write_file(filename: str, text: str, append: bool = False): Writes or appends the given content to the specified file in the workspace. Accepts either 'content' or 'text' parameter. If append=True, adds to the existing file; if append=False (default), overwrites the file. Returns a success or error message.
- list_files(directory: str = None): Lists all files in the workspace directory or a specified subdirectory. Returns a list of filenames.
- delete_file(filename: str): Deletes the specified file from the workspace directory. Returns a success or error message.
- execute_python(code: str, reset: bool = False): Executes the provided Python code snippet. Can be used for calculations, data manipulation, etc. Returns the output/result or error. Use standard libraries (os, json, requests, etc. are available). Print statements will be captured as output. Variables defined in one execution are available in subsequent executions. Set reset=True to clear all variables before execution. !!! CAUTION: Security risk if code is not controlled !!!
- reset_python_environment(): Resets the Python execution environment by clearing all stored variables. Returns a success message.
- list_python_variables(): Lists all variables currently stored in the Python execution environment. Useful for debugging and seeing what variables are available for use in subsequent Python code executions.
- memory_get(key: str): Retrieves a value from memory by key (parameter name is `key`, **not** `memory_key`). The value persists across multiple queries in the same conversation. Returns the stored value or an error message if the key doesn't exist.
- memory_set(key: str, value: str): Stores a value in memory with the given key. The value persists across multiple queries in the same conversation. Returns a success message.
- memory_list(): Lists all keys currently stored in memory. Returns a comma-separated list of keys or a message indicating no keys are stored.

Text Processing Tools:
- text_extract_urls(text: str): Extracts all URLs from the provided text. Returns a list of extracted URLs.

Firecrawl Tools (Advanced Web Scraping):
- firecrawl_scrape(url: str, formats: list = None, extract_schema: dict = None, extract_prompt: str = None, parse_pdf: bool = True): Scrapes a URL using Firecrawl and returns the content in specified formats. Formats can include 'markdown', 'html', and 'json'. Can extract structured data using a schema or a prompt. Automatically parses PDF content when the URL points to a PDF file (set parse_pdf=False to disable).
- firecrawl_crawl(url: str, limit: int = 10, formats: list = None, exclude_paths: list = None, parse_pdf: bool = True): Crawls a website using Firecrawl and returns content from all crawled pages. Limit controls the maximum number of pages to crawl. Automatically parses PDF content when URLs point to PDF files (set parse_pdf=False to disable).
- firecrawl_map(url: str, include_sitemap: bool = True, exclude_subdomains: bool = False): Maps a website using Firecrawl and returns a list of all URLs.

Knowledge Base Tools:
- kb_add_web(url: str, title: str = None): Adds a web page to the knowledge base. The content is scraped and stored for future reference. Returns a success message with the entry ID and memory key.
- kb_add_file(filename: str, title: str = None): Adds a local markdown file to the knowledge base. Returns a success message with the entry ID and memory key.
- kb_list(): Lists all entries in the knowledge base with their details. Returns a formatted list of entries.
- kb_get(entry_id: str = None, memory_key: str = None): Gets the content of a knowledge base entry by ID or memory key. Returns the content of the entry.
- kb_delete(entry_id: str): Deletes an entry from the knowledge base. Returns a success message.
- kb_search(query: str): Searches the knowledge base for entries matching the query. Returns a list of matching entries.
"""

# --- Configuration Lock ---
config_lock = threading.Lock()

# --- Configuration Functions ---
def load_model_config():
    """Load model configuration from file or return defaults."""
    try:
        if not os.path.exists(MODEL_CONFIG_FILE):
            return DEFAULT_MODELS.copy()
        with open(MODEL_CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Validate keys
        for key in DEFAULT_MODELS:
            if key not in data or not isinstance(data[key], str) or not data[key]:
                data[key] = DEFAULT_MODELS[key]
        return data
    except Exception:
        return DEFAULT_MODELS.copy()

def save_model_config(session_state):
    """Save model configuration to file."""
    try:
        to_save = {}
        for key in DEFAULT_MODELS:
            to_save[key] = session_state.get(key, DEFAULT_MODELS[key])
        with config_lock:
            with open(MODEL_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(to_save, f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save model configuration: {e}")
        return False

# --- Ensure workspace directory exists ---
if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)
