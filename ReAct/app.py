import streamlit as st
import os
import json
import re
from datetime import datetime

def generate_title(messages, client=None):
    """Generate a title based on the conversation messages using the configured LLM model."""
    try:
        # Extract the user's query from messages
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]

        # If we have user messages and a client, use the configured model to generate a title
        if user_messages and client:
            # Combine up to the last 3 user messages for context
            context = "\n".join(user_messages[-3:])

            # Use the configured model to generate a title
            try:
                # Get the title model from session state, with fallback to default
                title_model = st.session_state.get('title_model')

                completion = client.chat.completions.create(
                    model=title_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates concise, descriptive titles for conversations. Create a short title (5-7 words max) that captures the essence of the conversation."},
                        {"role": "user", "content": f"Generate a short, descriptive title for this conversation:\n{context}"}
                    ],
                    temperature=0.3,
                    max_tokens=20
                )

                if completion and completion.choices and completion.choices[0].message.content:
                    title = completion.choices[0].message.content.strip()
                    # Remove quotes if the model added them
                    title = title.strip('"\'')
                    return title
            except Exception as e:
                st.write(f"Error using Gemini for title generation: {str(e)}")
                # Fall back to simple title generation

        # Simple title generation fallback
        if user_messages:
            # Get the most recent user message
            latest_user_message = user_messages[-1]

            # Create a simple title from the first 30 characters of the message
            if len(latest_user_message) > 30:
                title = latest_user_message[:30] + "..."
            else:
                title = latest_user_message

            return title
        else:
            # Fallback to timestamp if no user messages
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            return f"Chat on {timestamp_str}"
    except Exception as e:
        st.write(f"Error generating title: {str(e)}")
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        return f"Chat on {timestamp_str}"

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from tavily import TavilyClient
import io
import contextlib
import traceback
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# --- Persistent Model Config Management ---
import threading
MODEL_CONFIG_FILE = "model_config.json"
DEFAULT_MODELS = {
    "planner_model": "google/gemini-2.0-flash-thinking-exp:free",
    "executor_model": "google/gemini-2.0-flash-exp:free",
    "summarizer_model": "google/gemini-2.0-flash-thinking-exp:free",
    "title_model": "google/gemini-2.0-flash-exp:free"
}

config_lock = threading.Lock()

def load_model_config():
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

def save_model_config():
    try:
        to_save = {}
        for key in DEFAULT_MODELS:
            to_save[key] = st.session_state.get(key, DEFAULT_MODELS[key])
        with config_lock:
            with open(MODEL_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(to_save, f, indent=2)
    except Exception as e:
        st.warning(f"Failed to save model configuration: {e}")
import time
import random
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
        tuple: (is_scrape_request, url, memory_key)
            - is_scrape_request (bool): True if the query is asking to scrape a URL
            - url (str): The URL to scrape, or None if no URL found
            - memory_key (str): Suggested memory key for storing the scraped content
    """
    # Common phrases that indicate a URL scrape request
    scrape_phrases = [
        "scrape", "extract", "get content", "get information",
        "use as knowledge", "use as reference", "use this url",
        "use this website", "use this link", "use this page",
        "read this website", "read this url", "read this link", "read this page"
    ]

    # Check if any scrape phrase is in the query (case insensitive)
    is_scrape_request = any(phrase.lower() in query.lower() for phrase in scrape_phrases)

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

    return (is_scrape_request, url, memory_key)

# --- Configuration & Constants ---
load_dotenv() # Load .env file if it exists
WORKSPACE_DIR = "agent_workspace"
if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)

# --- Tool Implementations ---

# Initialize debug mode in session state if not present
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# Create a function for controlled logging
def log_debug(message):
    """Log debug information only if debug mode is enabled"""
    if st.session_state.debug_mode:
        st.write(message)

# Create a function for tool status updates
def update_tool_status(tool_name, **kwargs):
    """Update the status display with tool execution information"""
    # Always update the status indicator
    if 'status_container' in st.session_state and st.session_state.status_container is not None:
        params = ', '.join([f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in kwargs.items()])
        st.session_state.status_container.info(f"🔧 Using tool: {tool_name}({params})")
    # Log detailed information if debug mode is on
    if st.session_state.debug_mode:
        st.write(f"TOOL: {tool_name}({', '.join([f'{k}={v!r}' for k, v in kwargs.items()])})")

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
        from data_acquisition.process_search_results import process_search_results

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

def web_scrape(url: str = None, urls: str = None) -> str:
    """Scrapes the text content of a given URL or list of URLs using WebScraper class."""
    # Handle both parameter names (url and urls) for backward compatibility
    target_url = url if url is not None else urls
    update_tool_status("web_scrape", url=target_url)

    if target_url is None:
        return "Error: No URL provided. Please provide a URL using the 'url' parameter."

    from data_acquisition.news_scraper import WebScraper

    try:
        scraper = WebScraper()

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
                            results[single_url] = scraper.scrape_content(single_url)
                        return json.dumps(results)
                except json.JSONDecodeError:
                    # If it's not valid JSON, treat it as a single URL
                    return scraper.scrape_content(target_url)
            else:
                # It's a regular URL string
                return scraper.scrape_content(target_url)
        elif isinstance(target_url, list):
            # It's already a list of URLs
            results = {}
            for single_url in target_url:
                results[single_url] = scraper.scrape_content(single_url)
            return json.dumps(results)
        else:
            return f"Invalid URL format: {target_url}. Expected a string URL or a list of URLs."
    except Exception as e:
        return f"Failed to scrape {target_url}: {str(e)}"

def read_file(filename: str) -> str:
    """Reads content from a file in the workspace directory."""
    update_tool_status("read_file", filename=filename)
    filepath = os.path.join(WORKSPACE_DIR, filename)
    try:
        if not os.path.exists(filepath):
             return f"Error: File '{filename}' not found in workspace."
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file '{filename}': {e}"

def write_file(filename: str, content: str = None, text: str = None, append: bool = False) -> str:
    """Writes or appends content to a file in the workspace directory.

    Args:
        filename: The name of the file to write
        content: The content to write to the file (primary parameter)
        text: Alternative parameter name for content (for backward compatibility)
        append: If True, append to the file instead of overwriting it (default: False)
    """
    # Handle both 'content' and 'text' parameters for backward compatibility
    actual_content = content
    if actual_content is None and text is not None:
        actual_content = text

    if actual_content is None:
        return "Error: No content provided. Please provide either 'content' or 'text' parameter."

    mode = 'a' if append else 'w'  # Use append mode if requested
    action = "appended" if append else "wrote"

    update_tool_status("write_file", filename=filename, append=append)
    filepath = os.path.join(WORKSPACE_DIR, filename)
    try:
        with open(filepath, mode, encoding='utf-8') as f:
            f.write(actual_content)
        return f"Successfully {action} content to '{filename}'."
    except Exception as e:
        return f"Error writing file '{filename}': {e}"

def list_files(directory: str = None) -> str:
    """Lists files in the workspace directory or a subdirectory.

    Args:
        directory: Optional subdirectory within the workspace to list files from
    """
    if directory:
        update_tool_status("list_files", directory=directory)
        # Handle both absolute paths and relative paths within the workspace
        if os.path.isabs(directory):
            target_dir = directory
        else:
            target_dir = os.path.join(WORKSPACE_DIR, directory)
    else:
        update_tool_status("list_files")
        target_dir = WORKSPACE_DIR

    try:
        if not os.path.exists(target_dir):
            return f"Error: Directory '{target_dir}' not found."
        if not os.path.isdir(target_dir):
            return f"Error: '{target_dir}' is not a directory."

        files = os.listdir(target_dir)
        if not files:
            return f"Directory '{target_dir}' is empty."
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {e}"
def migrate_conversations_schema():
    """Scan and migrate legacy conversation JSON files to extended schema, and build index."""
    import os
    import json
    import re
    from datetime import datetime

    conv_dir = os.path.join(WORKSPACE_DIR, 'agent_workspace')
    index = []

    pattern = re.compile(r'^conversation_(\d{8}_\d{6})\.json$')

    try:
        files = os.listdir(conv_dir)
    except Exception:
        files = []

    for fname in files:
        match = pattern.match(fname)
        if not match:
            continue

        timestamp_str = match.group(1)  # e.g., 20250404_092615
        dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        created_at = dt.isoformat()
        title = f"Chat on {dt.strftime('%Y-%m-%d %H:%M')}"

        fpath = os.path.join(conv_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            data = json.loads(content)
        except Exception:
            continue  # skip broken files

        # If already migrated (dict with 'messages' key), skip updating file
        if isinstance(data, dict) and 'messages' in data:
            schema = data
        elif isinstance(data, list):
            schema = {
                'title': title,
                'created_at': created_at,
                'messages': data
            }
            # Save back migrated schema
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2)
            except Exception:
                continue
        else:
            continue  # skip unknown formats

        index.append({
            'filename': fname,
            'title': schema.get('title', title),
            'created_at': schema.get('created_at', created_at)
        })

    # Save conversations_index.json
    index_path = os.path.join(conv_dir, 'conversations_index.json')
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
    except Exception:
        pass


def delete_file(filename: str) -> str:
    """Deletes a file from the workspace directory.

    Args:
        filename: The name of the file to delete
    """
    update_tool_status("delete_file", filename=filename)
    filepath = os.path.join(WORKSPACE_DIR, filename)
    try:
        if not os.path.exists(filepath):
            return f"Error: File '{filename}' not found in workspace."
        if not os.path.isfile(filepath):
            return f"Error: '{filename}' is not a file."
        os.remove(filepath)
        return f"Successfully deleted file '{filename}'."
    except Exception as e:
        return f"Error deleting file '{filename}': {e}"
def load_conversation(filename):
    import json
    path = os.path.join(WORKSPACE_DIR, 'agent_workspace', filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return []

    if isinstance(data, dict) and 'messages' in data:
        return data['messages']
    elif isinstance(data, list):
        return data
    else:
        return []


def save_conversation(filename, messages, title=None, created_at=None):
    import json
    from datetime import datetime
    import os

    conv_dir = os.path.join(WORKSPACE_DIR, 'agent_workspace')
    # Ensure the directory exists
    if not os.path.exists(conv_dir):
        os.makedirs(conv_dir)
    path = os.path.join(conv_dir, filename)

    if created_at is None:
        # Infer from filename timestamp
        try:
            ts_part = filename.split('_')[1] + '_' + filename.split('_')[2].split('.')[0]
            dt = datetime.strptime(ts_part, '%Y%m%d_%H%M%S')
            created_at = dt.isoformat()
        except Exception:
            created_at = datetime.now().isoformat()

    if title is None:
        try:
            dt = datetime.fromisoformat(created_at)
            title = f"Chat on {dt.strftime('%Y-%m-%d %H:%M')}"
        except Exception:
            title = "Chat"

    schema = {
        'title': title,
        'created_at': created_at,
        'messages': messages
    }

    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
    except Exception:
        return

    # Update conversations_index.json
    index_path = os.path.join(conv_dir, 'conversations_index.json')
    try:
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = []
    except Exception:
        index = []

    # Remove existing record with same filename
    index = [item for item in index if item.get('filename') != filename]
    index.append({
        'filename': filename,
        'title': title,
        'created_at': created_at
    })

    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
    except Exception:
        pass


def auto_save_conversation(messages, client, current_filename=None):
    """Automatically save conversation, either updating existing file or creating a new one."""
    if not messages or len(messages) == 0:
        return None, None

    # Determine if we should create a new file or update existing one
    if current_filename is None:
        # Create a new file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"
        created_at = datetime.now().isoformat()

        # Generate title using the configured model
        generated_title = generate_title(messages, client)

        # Save conversation with metadata
        save_conversation(filename, messages, title=generated_title, created_at=created_at)

        # Show a toast notification
        st.toast(f"Saved new conversation: {generated_title}", icon="✅")

        return filename, generated_title
    else:
        # Update existing file
        conv_dir = os.path.join(WORKSPACE_DIR, 'agent_workspace')
        path = os.path.join(conv_dir, current_filename)

        # Read existing data to preserve title and created_at
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                title = data.get('title', None)
                created_at = data.get('created_at', None)
        except Exception:
            # If file doesn't exist or is corrupted, create new metadata
            title = None
            created_at = None

        # Save updated conversation
        save_conversation(current_filename, messages, title=title, created_at=created_at)

        # Show a toast notification
        st.toast(f"Updated conversation", icon="✅")

        return current_filename, title


def execute_python(code: str) -> str:
    """
    Executes a Python code snippet.
    !!! DANGER ZONE: This uses exec() and is NOT secure. For demo only. !!!
    Requires a secure sandboxed environment for production.
    """
    st.warning("**Security Warning:** Executing Python code dynamically. Ensure code is safe! (Using `exec`)")
    update_tool_status("execute_python")
    st.code(code, language='python')

    local_vars = {}
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(code, globals(), local_vars)

        stdout = stdout_capture.getvalue()
        stderr = stderr_capture.getvalue()

        result = "Execution successful."
        if stdout:
            result += f"\nOutput:\n{stdout}"
        if stderr:
            result += f"\nErrors:\n{stderr}"
        # You might want to return specific variables from local_vars if needed
        # result += f"\nLocal variables: {local_vars}"
        return result

    except Exception as e:
        st.error(f"Python execution failed: {traceback.format_exc()}")
        return f"Error executing Python code: {e}\n{traceback.format_exc()}"

# --- Tool Dictionary ---
def get_stock_data(symbol: str = None, ticker: str = None, stock_symbol: str = None) -> str:
    """Fetches real-time stock data using Alpha Vantage API
    Accepts 'symbol', 'ticker', or 'stock_symbol' parameter for backward compatibility.
    """
    # Handle multiple parameter names for backward compatibility
    # Try each parameter in order of preference
    actual_symbol = symbol
    if actual_symbol is None:
        actual_symbol = ticker
    if actual_symbol is None:
        actual_symbol = stock_symbol

    update_tool_status("get_stock_data", symbol=actual_symbol)

    if actual_symbol is None:
        return json.dumps({'error': 'No stock symbol provided. Please provide a symbol using one of these parameters: "symbol", "ticker", or "stock_symbol"'})

    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        return json.dumps({'error': 'ALPHA_VANTAGE_API_KEY not found in environment variables'})

    try:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={actual_symbol}&apikey={api_key}'
        response = requests.get(url)
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({'error': f'API request failed: {str(e)}'})

# Define memory tool functions
def memory_get(key: str) -> str:
    """Retrieves a value from memory by key."""
    update_tool_status("memory_get", key=key)
    value = st.session_state.context.get(key, None)
    if value is None:
        return f"No value found for key '{key}' in memory."
    return str(value)

def memory_set(key: str, value: str) -> str:
    """Stores a value in memory with the given key."""
    update_tool_status("memory_set", key=key, value=value)
    st.session_state.context[key] = value
    return f"Successfully stored value for key '{key}' in memory."

def memory_list() -> str:
    """Lists all keys currently stored in memory."""
    update_tool_status("memory_list")
    # Filter out step results to only show named memory items
    memory_keys = [key for key in st.session_state.context.keys() if not key.startswith('step_')]
    if not memory_keys:
        return "No named memory items found."
    return "Memory keys: " + ", ".join(memory_keys)

# Functions for message-based memory management
def update_message_memory(message_index, remember=True):
    """Update whether a message should be remembered or not."""
    if 0 <= message_index < len(st.session_state.messages):
        message = st.session_state.messages[message_index]
        st.session_state.message_memories[message_index] = {
            "content": message["content"],
            "role": message["role"],
            "remember": remember
        }
        # Update the persistent memory with message content
        update_memory_from_messages()
        return True
    return False

def update_memory_from_messages():
    """Extract information from messages and update the persistent memory."""
    # Clear previous message-based memories
    # First, identify keys that were from messages
    message_memory_keys = [k for k in st.session_state.persistent_memory.keys()
                          if k.startswith('message_')]
    # Remove these keys
    for key in message_memory_keys:
        if key in st.session_state.persistent_memory:
            del st.session_state.persistent_memory[key]

    # Add memories from messages that should be remembered
    for idx, memory_data in st.session_state.message_memories.items():
        if memory_data["remember"] and memory_data["role"] == "assistant":
            # Only remember assistant messages
            memory_key = f"message_{idx}"
            st.session_state.persistent_memory[memory_key] = memory_data["content"]

    # Update context with the new memory state
    st.session_state.context = st.session_state.persistent_memory.copy()

TOOLS = {
    "web_search": web_search,
    "web_scrape": web_scrape,
    "get_stock_data": get_stock_data,
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "delete_file": delete_file,
    "execute_python": execute_python,
    "memory_get": memory_get,
    "memory_set": memory_set,
    "memory_list": memory_list,
}

TOOL_DESCRIPTIONS = """
Available Tools:
- web_search(query: str): Searches the web for the given query. Returns a list of search results (title, url, snippet).
- web_scrape(url: str): Fetches and extracts the main text content from a given URL or list of URLs. Returns the text content or a JSON object with URLs as keys and content as values. You can also directly ask to scrape a URL and use it as knowledge in the conversation (e.g., "Please scrape https://example.com and use it as knowledge").
- get_stock_data(symbol: str) or get_stock_data(ticker: str) or get_stock_data(stock_symbol: str): Fetches real-time stock data for the given stock symbol using Alpha Vantage API. Returns stock information in JSON format.
- read_file(filename: str): Reads the content of the specified file from the workspace. Returns the file content.
- write_file(filename: str, content: str, append: bool = False) or write_file(filename: str, text: str, append: bool = False): Writes or appends the given content to the specified file in the workspace. Accepts either 'content' or 'text' parameter. If append=True, adds to the existing file; if append=False (default), overwrites the file. Returns a success or error message.
- list_files(directory: str = None): Lists all files in the workspace directory or a specified subdirectory. Returns a list of filenames.
- delete_file(filename: str): Deletes the specified file from the workspace directory. Returns a success or error message.
- execute_python(code: str): Executes the provided Python code snippet. Can be used for calculations, data manipulation, etc. Returns the output/result or error. Use standard libraries (os, json, requests, etc. are available). Print statements will be captured as output. !!! CAUTION: Security risk if code is not controlled !!!
- memory_get(key: str): Retrieves a value from memory by key (parameter name is `key`, **not** `memory_key`). The value persists across multiple queries in the same conversation. Returns the stored value or an error message if the key doesn't exist.
- memory_set(key: str, value: str): Stores a value in memory with the given key. The value persists across multiple queries in the same conversation. Returns a success message.
- memory_list(): Lists all keys currently stored in memory. Returns a comma-separated list of keys or a message indicating no keys are stored.
"""

# --- LLM Interaction ---

def get_openai_client(api_key, base_url="https://openrouter.ai/api/v1"):
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=base_url)

def validate_and_assess_plan(plan_list, query_complexity):
    """Validates plan structure and assesses overall complexity.

    Args:
        plan_list (list): The plan steps list to validate
        query_complexity (str): The complexity level of the original query

    Returns:
        list: The validated and potentially enhanced plan
    """
    if not plan_list or len(plan_list) == 0:
        st.error("Empty plan generated. Please try again.")
        return []

    # Check for required keys in each step
    for i, step in enumerate(plan_list):
        if not all(k in step for k in ["step_id", "description", "tool_suggestion", "dependencies", "status", "result"]):
            st.warning(f"Step {i+1} is missing required keys. Fixing...")
            # Add missing keys with default values
            if "step_id" not in step:
                step["step_id"] = i + 1
            if "description" not in step:
                step["description"] = f"Step {i+1}"
            if "tool_suggestion" not in step:
                step["tool_suggestion"] = "None"
            if "dependencies" not in step:
                step["dependencies"] = []
            if "status" not in step:
                step["status"] = "Pending"
            if "result" not in step:
                step["result"] = None

        # Ensure step_ids are sequential
        step["step_id"] = i + 1
        step["status"] = "Pending"
        step["result"] = None

    # Assess plan complexity
    plan_complexity = "Low"
    if len(plan_list) > 7:
        plan_complexity = "Medium"
    if len(plan_list) > 12:
        plan_complexity = "High"

    # Check for non-linear dependencies (increases complexity)
    for step in plan_list:
        if len(step.get("dependencies", [])) > 1:
            # Upgrade complexity level if multiple dependencies exist
            if plan_complexity == "Low":
                plan_complexity = "Medium"
            elif plan_complexity == "Medium":
                plan_complexity = "High"

    # Check for circular dependencies
    dependency_graph = {step["step_id"]: step["dependencies"] for step in plan_list}
    if has_circular_dependencies(dependency_graph):
        st.warning("Plan contains circular dependencies. Fixing...")
        # Fix circular dependencies by removing problematic ones
        for step in plan_list:
            # Simple fix: ensure dependencies only point to earlier steps
            step["dependencies"] = [dep for dep in step["dependencies"] if dep < step["step_id"]]

    # Log plan assessment
    log_debug(f"Plan complexity assessment: {plan_complexity} (Query complexity: {query_complexity})")
    if plan_complexity == "High":
        st.session_state.status_container.info(f"🧠 Complex plan with {len(plan_list)} steps. Execution may take longer.")

    return plan_list

def has_circular_dependencies(dependency_graph):
    """Check if the dependency graph has circular dependencies.

    Args:
        dependency_graph (dict): Dictionary mapping step_id to list of dependencies

    Returns:
        bool: True if circular dependencies exist, False otherwise
    """
    visited = set()
    path = set()

    def dfs(node):
        visited.add(node)
        path.add(node)

        for neighbor in dependency_graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in path:
                return True

        path.remove(node)
        return False

    for node in dependency_graph:
        if node not in visited:
            if dfs(node):
                return True

    return False

def assess_query_complexity(query: str) -> str:
    """Assess the complexity of a user query based on various factors.

    Returns:
        str: Complexity level - "Low", "Medium", or "High"
    """
    # Simple heuristic-based assessment
    complexity_indicators = [
        "compare", "analyze", "multiple", "several", "complex",
        "relationship", "between", "and then", "afterwards",
        "first", "second", "third", "finally", "if", "else", "otherwise",
        "depending", "based on", "versus", "vs", "different", "similar",
        "pros and cons", "advantages", "disadvantages", "benefits", "drawbacks"
    ]

    # Count sentences
    sentences = [s for s in query.split('.') if s.strip()]

    # Count complexity indicators
    indicator_count = sum(1 for indicator in complexity_indicators if indicator.lower() in query.lower())

    # Count question marks (multiple questions indicate complexity)
    question_count = query.count('?')

    # Assess complexity
    if (len(sentences) > 3 or
        indicator_count > 2 or
        len(query.split()) > 50 or
        question_count > 1):
        return "High"
    elif (len(sentences) > 1 or
          indicator_count > 0 or
          len(query.split()) > 20 or
          question_count > 0):
        return "Medium"
    else:
        return "Low"

def run_planner(client: OpenAI, user_query: str, planner_model: str) -> list:
    """Generates the initial plan using the Planner LLM. Always returns a list."""
    if not client:
        st.error("API key not configured. Cannot run Planner.")
        return []

    # Assess query complexity
    complexity = assess_query_complexity(user_query)
    log_debug(f"Query complexity assessment: {complexity}")

    # Adjust temperature based on complexity
    temperature = 0.2  # Default
    if complexity == "High":
        temperature = 0.1  # Lower temperature for more deterministic output on complex queries
        st.session_state.status_container.info("🧠 Complex query detected. Using enhanced planning...")

    # Get the current memory state to include in the prompt
    memory_info = ""
    if st.session_state.persistent_memory:
        # Separate message memories from other memories for better organization
        message_keys = [k for k in st.session_state.persistent_memory.keys() if k.startswith('message_')]
        other_keys = [k for k in st.session_state.persistent_memory.keys() if not k.startswith('message_')]

        memory_sections = []

        # Add message memories if available
        if message_keys:
            message_section = "\n\nYou have access to the following information from previous messages:\n"
            for key in message_keys:
                # Extract the message index from the key
                idx = key.split('_')[1]
                message_section += f"- Previous response {idx}: Use memory_get(\"{key}\") to access\n"
            memory_sections.append(message_section)

        # Add other memories if available
        if other_keys:
            other_section = "\n\nYou have access to the following memory items from previous interactions:\n"
            for key in other_keys:
                other_section += f"- {key}: Use memory_get(\"{key}\") to access\n"
            memory_sections.append(other_section)

        # Combine all memory sections
        if memory_sections:
            memory_info = ''.join(memory_sections)

    system_prompt = f"""You are a meticulous planning agent. Your task is to break down the user's query into a sequence of actionable steps.
Today's Date: {datetime.now().strftime('%Y-%m-%d')}
You have access to the following tools:
{TOOL_DESCRIPTIONS}

**IMPORTANT FOR FILE OPERATIONS:**
- When the user wants to ADD, APPEND, or UPDATE content in an existing file, plan to use `write_file` with `append=true`
- When the user wants to CREATE a new file or REPLACE/OVERWRITE an existing file, plan to use `write_file` with `append=false` (default)
- When the user wants to DELETE or REMOVE a file, plan to use `delete_file` with the filename
- Examples where `append=true` is needed: "add a line to file.txt", "append text to file.txt", "update file.txt with new content"
- After performing a web search, URLs are extracted and stored in memory under the key "search_result_urls". Use `memory_get("search_result_urls")` to retrieve the list of URLs for scraping or further processing.

- Examples where `delete_file` is needed: "delete file.txt", "remove file.txt", "erase file.txt"

**IMPORTANT FOR WEB SCRAPING AND KNOWLEDGE:**
- When the user wants to scrape a URL and use it as knowledge, plan to use `web_scrape` to get the content and then `memory_set` to store it
- After scraping a URL, store the content in memory with a descriptive key like "scraped_[domain]" for future reference
- When answering questions about previously scraped content, plan to use `memory_get` to retrieve the stored content

**IMPORTANT FOR MEMORY OPERATIONS:**
- Use memory_get, memory_set, and memory_list tools to maintain information across multiple queries
- When the user refers to information from previous interactions, plan to use memory_get to retrieve it
- When you discover information that might be useful in future queries, plan to use memory_set to store it{memory_info}

**GUIDELINES FOR COMPLEX QUERIES:**
- For multi-part queries, break down each part into separate steps with clear dependencies
- For data-intensive tasks, include steps for data validation and error handling
- For tasks requiring multiple sources, plan to gather all information before synthesis
- For tasks with potential failure points, include fallback steps or verification steps
- For tasks requiring comparisons or analysis, break down into data gathering, analysis, and synthesis steps
- For tasks involving multiple tools in sequence, ensure proper data flow between steps
- For tasks with conditional logic, create separate steps for each condition and use dependencies appropriately
- For tasks requiring iterative processing, create steps that can handle batches or chunks of data
- For tasks with ambiguity, include steps to clarify requirements or validate assumptions

Based on the user query: "{user_query}"

Generate a structured plan as a JSON list of objects. Each object represents a step and must have the following keys:
- "step_id": A unique integer identifier for the step (starting from 1).
- "description": A clear, concise instruction for what needs to be done in this step.
- "tool_suggestion": The name of the *most likely* tool to be used for this step (must be one of the available tools). If no specific tool is needed (e.g., final reasoning/compilation), suggest "None".
- "dependencies": A list of `step_id`s that must be completed *before* this step can start. Empty list `[]` if no dependencies.
- "status": Initialize this to "Pending".
- "result": Initialize this to `null`.

Ensure the plan is logical, sequential, and covers all aspects of the user query. The final step should typically involve compiling or presenting the result.
Output *only* the JSON list, nothing else before or after.
"""
    try:
        completion = client.chat.completions.create(
            model=planner_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=temperature,  # Use complexity-based temperature
            response_format={"type": "json_object"} # Request JSON output if model supports it
        )
        response_content = completion.choices[0].message.content
        # Sometimes the response might be wrapped in ```json ... ```, try to extract
        if response_content.strip().startswith("```json"):
             response_content = response_content.strip()[7:-3].strip()
        # The model might return a dict with a key like "plan"
        parsed_json = json.loads(response_content)
        if isinstance(parsed_json, dict) and len(parsed_json) == 1:
             plan_list = list(parsed_json.values())[0] # Get the list if it's nested
        elif isinstance(parsed_json, list):
             plan_list = parsed_json
        else:
             raise ValueError("Planner did not return a JSON list.")

        # Validate and assess plan structure
        plan_list = validate_and_assess_plan(plan_list, complexity)
        return plan_list
    except json.JSONDecodeError as e:
        st.error(f"Planner Error: Failed to decode JSON response: {e}\nResponse received:\n{response_content}")
        return []
    except Exception as e:
        st.error(f"Planner Error: An unexpected error occurred: {e}\n{traceback.format_exc()}")
        return []


def run_executor_step(client: OpenAI, step: dict, context: dict, executor_model: str) -> tuple[str, str, str]:
    """Executes a single step using the Executor LLM and tools (simulates ReAct)."""
    if not client:
        return "Error: API Client not initialized.", "Error", "Cannot run Executor (API key missing?)."

    step_desc = step['description']
    tool_suggestion = step['tool_suggestion']

    # --- Reason Phase ---
    reasoning_prompt = f"""You are an execution agent. Your goal is to perform the action described in the current step.
Current Step: "{step_desc}"
Suggested Tool: {tool_suggestion}
Available Tools: {list(TOOLS.keys())}
Context from previous steps: {json.dumps(context, indent=2)}

1.  **Reason:** Analyze the step description and context. Decide which tool is *best* suited to accomplish this step. If a tool is needed, determine the *exact* arguments required, drawing information from the context if necessary. Pay close attention to the parameter names expected by each tool.

   **REQUIRED PARAMETERS FOR TOOLS:**
   - `web_search` requires a `query` parameter (string)
   - `web_scrape` requires a `url` parameter (string)
   - `get_stock_data` requires a `symbol` parameter (string)
   - `read_file` requires a `filename` parameter (string)
   - `write_file` requires `filename` (string) and `content` (string) parameters, with optional `append` (boolean)
   - `list_files` has an optional `directory` parameter (string)
   - `delete_file` requires a `filename` parameter (string)
   - `execute_python` requires a `code` parameter (string)
   - `memory_get` requires a `key` parameter (string) - NOT `memory_key`
   - `memory_set` requires `key` (string) and `value` (string) parameters
   - `memory_list` takes no parameters

   **IMPORTANT FOR FILE OPERATIONS:**
   - When the user wants to ADD, APPEND, or UPDATE content in an existing file, use `write_file` with `append=true`
   - When the user wants to CREATE a new file or REPLACE/OVERWRITE an existing file, use `write_file` with `append=false` (default)
   - When the user wants to DELETE or REMOVE a file, use `delete_file` with the filename
   - Examples where `append=true` is needed: "add a line to file.txt", "append text to file.txt", "update file.txt with new content"
   - Examples where `delete_file` is needed: "delete file.txt", "remove file.txt", "erase file.txt"

   **IMPORTANT FOR WEB SCRAPING AND KNOWLEDGE:**
   - When scraping a URL for knowledge, use `web_scrape` to get the content and then `memory_set` to store it
   - After scraping a URL, store the content in memory with a descriptive key like "scraped_[domain]" for future reference
   - When answering questions about previously scraped content, use `memory_get` to retrieve the stored content

   If no tool is needed (e.g., summarizing context), decide on the action.
2.  **Action Format:** Respond with a JSON object containing the chosen tool and its arguments. The format *must* be:
    `{{"tool": "tool_name", "args": {{"arg_name1": "value1", "arg_name2": "value2", "reasoning": "Your detailed reasoning here"}}}}`

    Always include a "reasoning" field in the args object that explains your thought process.

    If no tool is needed for this step (e.g., the step is just about reasoning or formatting based on context), use:
    `{{"tool": "None", "args": {{"comment": "Reasoning or action description", "reasoning": "Your detailed reasoning here"}}}}`

Provide *only* the JSON object as your response.
"""
    reasoning = "Reasoning not initiated."
    action_json_str = ""
    action_str = "Error" # Default action string
    observation = "Execution did not proceed." # Default observation

    # We'll extract the reasoning from the LLM response later

    try:
        log_debug(f"Attempting LLM call for step: {step_desc}") # Debug output
        completion = client.chat.completions.create(
            model=executor_model,
            messages=[
                {"role": "system", "content": reasoning_prompt},
                {"role": "user", "content": f"Execute step: {step_desc}"}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        log_debug(f"LLM call completed. Completion object: {completion}") # Debug output

        # --- ROBUSTNESS CHECKS ---
        if not completion:
            reasoning = "Executor Error: LLM API call returned None object."
            st.error(reasoning)
            return reasoning, action_str, "LLM API response invalid (None completion)."

        if not completion.choices:
            reasoning = "Executor Error: LLM API call returned no 'choices'."
            st.error(reasoning)
            st.error(f"Raw completion: {completion}")
            return reasoning, action_str, "LLM API response invalid (no choices)."

        if len(completion.choices) == 0:
            reasoning = "Executor Error: LLM API call returned empty 'choices' list."
            finish_reason = completion.usage if hasattr(completion, 'usage') else 'N/A' # Check if usage info exists, maybe finish reason is there?
            st.error(reasoning)
            st.error(f"Raw completion: {completion}")
            st.warning(f"Potentially check finish reason if available: {finish_reason}")
            return reasoning, action_str, "LLM API response invalid (empty choices)."

        choice = completion.choices[0]
        if choice.message is None or choice.message.content is None:
            finish_reason = choice.finish_reason if hasattr(choice, 'finish_reason') else 'N/A'
            reasoning = f"Executor Error: LLM API response missing 'message' or 'content'. Finish Reason: {finish_reason}"
            st.error(reasoning)
            st.error(f"Raw completion: {completion}")
            if finish_reason == 'content_filter':
                 st.warning("Content filter likely triggered.")
                 observation = f"LLM refused to respond due to content filter (Finish Reason: {finish_reason})."
            else:
                 observation = f"LLM API response invalid (missing content). Finish Reason: {finish_reason}"
            return reasoning, action_str, observation

        action_json_str = choice.message.content
        log_debug(f"Raw action JSON: {action_json_str}") # Debug output

        # Extract reasoning from the LLM response
        # The LLM should be thinking about the reasoning in its internal process
        # before generating the action JSON, so we'll consider the content as containing
        # the reasoning implicitly

        # Parse action JSON
        try:
            action = json.loads(action_json_str)

            # Validate the action JSON structure
            if not isinstance(action, dict):
                reasoning = "Executor Error: Action must be a JSON object/dictionary"
                st.error(reasoning)
                return reasoning, "Error", "Invalid action format: not a JSON object"

            # Check for required fields
            if 'tool' not in action:
                reasoning = "Executor Error: Missing 'tool' field in action JSON"
                st.error(reasoning)
                return reasoning, "Error", "Missing 'tool' field in action"

            if 'args' not in action or not isinstance(action['args'], dict):
                reasoning = "Executor Error: Missing or invalid 'args' field in action JSON"
                st.error(reasoning)
                return reasoning, "Error", "Missing or invalid 'args' field in action"

            # Update reasoning with the actual reasoning from the LLM
            # Extract reasoning from the 'reasoning' field in args if available
            if action['tool'] == 'None':
                action_str = action['args'].get('comment', 'No action required')
                reasoning = action['args'].get('reasoning', action['args'].get('comment', 'No explicit reasoning provided'))
            else:
                # Remove reasoning from the displayed action string to avoid duplication
                action_args = action['args'].copy()
                extracted_reasoning = action_args.pop('reasoning', None)
                action_str = f"{action['tool']}({json.dumps(action_args)})"

                # Use the extracted reasoning if available, otherwise construct a default one
                if extracted_reasoning:
                    reasoning = extracted_reasoning
                else:
                    reasoning = f"Based on the step description, I need to use the {action['tool']} tool with the following parameters: {json.dumps(action_args, indent=2)}"
        except json.JSONDecodeError as e:
            reasoning = f"Executor Error: Invalid JSON response from LLM: {e}"
            st.error(reasoning)
            st.error(f"Invalid JSON content: {action_json_str}")
            return reasoning, "Error", "Invalid action JSON format"
        except KeyError as e:
            reasoning = f"Executor Error: Missing required key in action JSON: {e}"
            st.error(reasoning)
            st.error(f"Malformed action JSON: {action_json_str}")
            return reasoning, "Error", "Malformed action JSON structure"

        # --- Execute Tool ---
        try:
            if action['tool'] != "None":
                # Remove the reasoning field from args before passing to the tool function
                tool_args = action['args'].copy()
                if 'reasoning' in tool_args:
                    tool_args.pop('reasoning')
                # Compatibility fix: remap 'memory_key' to 'key' if present for memory_get
                if action['tool'] == "memory_get":
                    if 'memory_key' in tool_args:
                        tool_args['key'] = tool_args.pop('memory_key')
                    # Ensure key parameter exists for memory_get
                    if 'key' not in tool_args or not tool_args['key']:
                        raise ValueError("memory_get requires a 'key' parameter")

                log_debug(f"\n\nAttempting to execute: {action['tool']} with args {tool_args}")

                if action['tool'] not in TOOLS:
                    raise ValueError(f"Tool '{action['tool']}' not registered in TOOLS dictionary")

                tool_func = TOOLS[action['tool']]

                # Validate arguments are in keyword form
                if not isinstance(tool_args, dict):
                    raise TypeError(f"Tool arguments must be dictionary, got {type(tool_args).__name__}")

                # Check for required arguments based on tool type
                if action['tool'] == "memory_get" and ('key' not in tool_args or not tool_args['key']):
                    raise ValueError("memory_get requires a 'key' parameter")
                elif action['tool'] == "memory_set" and ('key' not in tool_args or 'value' not in tool_args):
                    raise ValueError("memory_set requires both 'key' and 'value' parameters")
                elif action['tool'] == "web_search" and ('query' not in tool_args or not tool_args['query']):
                    raise ValueError("web_search requires a 'query' parameter")

                observation = tool_func(**tool_args)
                st.success(f"Tool execution completed: {action['tool']}")
            else:
                # For 'None' tool, we just need the comment as observation
                # Make sure we don't include the reasoning field in the observation
                observation = action['args'].get('comment', 'No action required')
        except Exception as e:
            reasoning = f"Tool execution error: {str(e)}"
            st.error(reasoning)
            st.error(traceback.format_exc())
            return reasoning, action_str, f"Tool execution failed: {str(e)}"

        return reasoning, action_str, observation

    except Exception as e:
        reasoning = f"Executor Error: Unexpected error during execution - {str(e)}"
        st.error(reasoning)
        st.error(traceback.format_exc())
        return reasoning, "Error", f"Unexpected error: {str(e)}"

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("📄 Plan-ReAct Agent")
st.markdown("---")

# --- Configuration Sidebar ---
# --- Initialize persistent model configs ---
model_config = load_model_config()

if 'planner_model' not in st.session_state:
    st.session_state.planner_model = model_config.get('planner_model', DEFAULT_MODELS['planner_model'])
if 'executor_model' not in st.session_state:
    st.session_state.executor_model = model_config.get('executor_model', DEFAULT_MODELS['executor_model'])
if 'summarizer_model' not in st.session_state:
    st.session_state.summarizer_model = model_config.get('summarizer_model', DEFAULT_MODELS['summarizer_model'])
if 'title_model' not in st.session_state:
    st.session_state.title_model = model_config.get('title_model', DEFAULT_MODELS['title_model'])

# Other session variables
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("OPENROUTER_API_KEY", "")
if 'base_url' not in st.session_state:
    st.session_state.base_url = "https://openrouter.ai/api/v1"
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("OPENROUTER_API_KEY", "")
if 'base_url' not in st.session_state:
    st.session_state.base_url = "https://openrouter.ai/api/v1"
if 'planner_model' not in st.session_state:
    st.session_state.planner_model = "google/gemini-2.0-flash-thinking-exp:free"
if 'executor_model' not in st.session_state:
    st.session_state.executor_model = "google/gemini-2.0-flash-exp:free"
if 'summarizer_model' not in st.session_state:
    st.session_state.summarizer_model = "google/gemini-2.0-flash-thinking-exp:free"
if 'title_model' not in st.session_state:
    st.session_state.title_model = "google/gemini-2.0-flash-exp:free"

page = st.sidebar.radio("Sidebar Pages", ["Configuration", "Conversation Management"], index=1)

if page == "Configuration":
    # Main Configuration Section
    st.sidebar.subheader("Configuration")

    # API Configuration
    st.session_state.api_key = st.sidebar.text_input("OpenRouter API Key", type="password", value=st.session_state.api_key)
    st.session_state.base_url = st.sidebar.text_input("OpenRouter API Base", value=st.session_state.base_url)

    # LLM Models Configuration in a collapsible section
    with st.sidebar.expander("🤖 LLM Models", expanded=False):
        st.session_state.planner_model = st.text_input("Planner Model", value=st.session_state.planner_model)
        st.session_state.executor_model = st.text_input("Executor Model", value=st.session_state.executor_model)
        st.session_state.summarizer_model = st.text_input("Summarizer Model", value=st.session_state.summarizer_model)
        st.session_state.title_model = st.text_input("Title Generation Model", value=st.session_state.title_model)
    # Persist updated model selections
    save_model_config()
    st.sidebar.markdown("---")

    # Memory Management UI
    with st.sidebar.expander("🧠 Conversation Memory", expanded=False):
        # Display current memory items
        st.subheader("Current Memory Items")

        # Separate message memories from other memories
        message_memories = {k: v for k, v in st.session_state.persistent_memory.items() if k.startswith('message_')}
        other_memories = {k: v for k, v in st.session_state.persistent_memory.items() if not k.startswith('message_')}

        # Display message memories first
        if message_memories:
            st.markdown("### 💬 Message Memories")
            for key, value in message_memories.items():
                # Extract message index
                try:
                    msg_idx = int(key.split('_')[1])
                    # Get the original message if available
                    if 0 <= msg_idx < len(st.session_state.messages):
                        original_msg = st.session_state.messages[msg_idx]
                        st.markdown(f"**Message {msg_idx} ({original_msg['role']})**")
                        st.markdown(str(value)[:500] + ('...' if len(str(value)) > 500 else ''))
                    else:
                        st.markdown(f"**{key}**")
                        st.markdown(str(value)[:500] + ('...' if len(str(value)) > 500 else ''))
                except:
                    st.markdown(f"**{key}**")
                    st.markdown(str(value)[:500] + ('...' if len(str(value)) > 500 else ''))

        # Display other memories
        if other_memories:
            st.markdown("### 🔑 Custom Memories")
            for key, value in other_memories.items():
                st.markdown(f"**{key}**")
                st.markdown(str(value)[:500] + ('...' if len(str(value)) > 500 else ''))

        # Show message if no memories
        if not message_memories and not other_memories:
            st.info("No memory items stored yet.")

        # Add a button to clear all memory
        if message_memories or other_memories:
            if st.button("Clear All Memory"):
                st.session_state.persistent_memory = {}
                st.session_state.context = {}
                st.session_state.message_memories = {}
                st.success("Memory cleared successfully!")
                st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Tools Available:")
    st.sidebar.markdown(f"`{', '.join(TOOLS.keys())}`")
    st.sidebar.markdown("---")
    st.sidebar.warning("**Security Note:** `execute_python` uses `exec()` and is **not secure**. Use with extreme caution and only trusted code/inputs in a local, controlled environment.")

if page == "Conversation Management":
    # Modern styling for sidebar and conversation UI
    st.sidebar.markdown(
        """
        <style>
        /* Modern sidebar styling */
        .stButton button {
            padding: 0.4rem 0.6rem;
            font-size: 0.85rem;
            border-radius: 6px;
            transition: all 0.2s ease;
        }
        .stButton button:hover {
            transform: translateY(-1px);
        }
        .stDownloadButton button {
            padding: 0.4rem 0.6rem;
            font-size: 0.85rem;
            border-radius: 6px;
        }
        .stTextInput label, .stSelectbox label {
            font-size: 0.85rem;
            font-weight: 500;
        }
        .stSidebar .block-container {
            padding-top: 0.8rem;
            padding-bottom: 0.8rem;
        }

        /* Conversation cards styling */
        .conversation-card {
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 8px;
            border-left: 3px solid #4e8cff;
        }
        .conversation-timestamp {
            font-size: 0.75rem;
            margin-bottom: 4px;
        }
        .conversation-title {
            font-weight: 500;
            margin-bottom: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .conversation-actions {
            display: flex;
            gap: 6px;
            margin-top: 6px;
        }

        /* Chat message styling */
        .chat-message {
            padding: 10px 15px;
            border-radius: 12px;
            margin-bottom: 10px;
            max-width: 85%;
        }
        .user-message {
            /* Removed margin-left: auto to align with default Streamlit alignment */
            border-bottom-right-radius: 4px;
        }
        .assistant-message {
            margin-right: auto;
            border-bottom-left-radius: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Initialize OpenAI client
    client = get_openai_client(st.session_state.api_key, st.session_state.base_url)

    # Load conversation index metadata
    conv_index_path = os.path.join(WORKSPACE_DIR, "agent_workspace", "conversations_index.json")
    conversations = []
    try:
        with open(conv_index_path, "r", encoding="utf-8") as f:
            conversations = json.load(f)
            if not isinstance(conversations, list):
                conversations = []
    except Exception:
        conversations = []

    with st.sidebar.expander("📂 Conversations", expanded=True):
        st.button("➕ New Chat", key="new_chat_button",
                 on_click=lambda: st.session_state.update({
                     'messages': [],
                     'current_conversation_filename': None,
                     'persistent_memory': {},
                     'message_memories': {}
                 }),
                 use_container_width=True)

        if not conversations:
            st.info("No saved conversations found.")
        else:
            for conv in sorted(conversations, key=lambda x: x.get('created_at', ''), reverse=True):
                filename = conv.get('filename')
                title = conv.get('title', 'Untitled')
                created_at = conv.get('created_at', '')
                try:
                    dt_obj = datetime.fromisoformat(created_at)
                    timestamp_str = dt_obj.strftime('%Y-%m-%d %H:%M')
                except:
                    timestamp_str = created_at

                # Create a card-like container for each conversation
                with st.container():
                    # Display conversation card with title and timestamp
                    st.markdown(f"""<div class='conversation-card'>
                        <div class='conversation-timestamp'>{timestamp_str}</div>
                        <div class='conversation-title'>{title}</div>
                    </div>""", unsafe_allow_html=True)

                    # Action buttons in a single row
                    cols = st.columns([1, 1])

                    # Load button
                    if cols[0].button("📂 Load", key=f"load_{filename}", use_container_width=True):
                        conv_path = os.path.join(WORKSPACE_DIR, "agent_workspace", filename)
                        try:
                            with open(conv_path, "r", encoding="utf-8") as f:
                                data = json.load(f)

                            # Extract messages from the data
                            if isinstance(data, dict) and 'messages' in data:
                                st.session_state.messages = data['messages']
                            elif isinstance(data, list):
                                st.session_state.messages = data
                            else:
                                st.error("Invalid conversation format.")
                                continue

                            # Set the current conversation filename
                            st.session_state.current_conversation_filename = filename

                            st.success(f"Loaded: {title}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to load conversation: {e}")

                    # Delete button
                    if cols[1].button("🚮 Delete", key=f"delete_{filename}", use_container_width=True):
                        conv_path = os.path.join(WORKSPACE_DIR, "agent_workspace", filename)
                        try:
                            if os.path.exists(conv_path):
                                os.remove(conv_path)

                            # Remove from index and save
                            conversations = [c for c in conversations if c.get('filename') != filename]
                            with open(conv_index_path, "w", encoding="utf-8") as f:
                                json.dump(conversations, f, indent=2)

                            st.success("Conversation deleted.")
                            st.rerun()
                        except Exception as e:
                            st.warning(f"Failed to delete conversation: {e}")

                    st.markdown("<hr style='margin: 8px 0; opacity: 0.2;'>", unsafe_allow_html=True)

# Initialize client if not already done in the Conversation Management section
if 'client' not in locals():
    client = get_openai_client(st.session_state.api_key, st.session_state.base_url)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "plan" not in st.session_state:
    st.session_state.plan = None
if "current_step_index" not in st.session_state:
    st.session_state.current_step_index = -1
if "context" not in st.session_state: # Short-term memory for the current task
    st.session_state.context = {}
if "persistent_memory" not in st.session_state: # Cross-query persistent memory
    st.session_state.persistent_memory = {}
if "message_memories" not in st.session_state: # Track which messages are included in memory
    st.session_state.message_memories = {} # Format: {message_index: {"content": "...", "remember": True}}
if "execution_log" not in st.session_state:
    st.session_state.execution_log = [] # To show Reason/Act/Observe
if "current_conversation_filename" not in st.session_state:
    st.session_state.current_conversation_filename = None # Track current conversation file

# Display chat messages with modern styling
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        # Display message content directly without custom styling div
        st.markdown(message['content'])

        # Add memory toggle for assistant messages only
        if message["role"] == "assistant":
            # Check if this message is already in memory tracking
            is_remembered = True  # Default to True (include in memory)
            if idx in st.session_state.message_memories:
                is_remembered = st.session_state.message_memories[idx]["remember"]
            else:
                # Initialize memory for this message
                update_message_memory(idx, True)

            # Create columns for the toggle
            cols = st.columns([6, 1])
            with cols[1]:
                # Create a toggle for memory inclusion
                new_state = st.toggle(
                    "🧠",
                    value=is_remembered,
                    key=f"memory_toggle_{idx}",
                    help="Toggle to include/exclude this message from memory"
                )

                # Update memory if toggle state changed
                if new_state != is_remembered:
                    update_message_memory(idx, new_state)
                    st.rerun()

# Add styling for expanders
st.markdown("<style>.stExpander {border: none !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1);}</style>", unsafe_allow_html=True)

# Create containers for plan display and status updates
# These containers will not be displayed in the final output response to the user
plan_container = st.empty()
log_container = st.empty()

# Create a container for status updates
st.session_state.status_container = st.empty()

# Add debug mode toggle in sidebar
if page == "Configuration":
    with st.sidebar.expander("🐞 Debug Options", expanded=False):
        st.session_state.debug_mode = st.toggle("Enable Debug Mode", value=st.session_state.debug_mode)
        if st.session_state.debug_mode:
            st.info("Debug mode is enabled. Verbose output will be shown during execution.")
        else:
            st.info("Debug mode is disabled. Only essential status updates will be shown.")

# --- Orchestrator Logic ---
if st.session_state.plan is not None and 0 <= st.session_state.current_step_index < len(st.session_state.plan):
    current_step = st.session_state.plan[st.session_state.current_step_index]

    if current_step["status"] == "Pending":
        # Check dependencies (simple check: previous step must be completed)
        dependencies_met = True
        if current_step["dependencies"]:
            for dep_id in current_step["dependencies"]:
                # Find the dependent step
                dep_step = next((s for s in st.session_state.plan if s["step_id"] == dep_id), None)
                if not dep_step or dep_step["status"] != "Completed":
                    dependencies_met = False
                    # This state shouldn't normally be reached with sequential execution,
                    # but good for robustness if dependencies were complex.
                    st.warning(f"Step {current_step['step_id']} waiting for dependency {dep_id} which is {dep_step['status'] if dep_step else 'Not Found'}")
                    break # Stop execution for this cycle

        if dependencies_met:
            # Update the status container with the current step information
            st.session_state.status_container.info(f"⏳ Step {current_step['step_id']}/{len(st.session_state.plan)}: {current_step['description']}")
            with st.spinner(f"Running Step {current_step['step_id']}/{len(st.session_state.plan)}..."):
                reasoning, action_str, observation = run_executor_step(
                    client, current_step, st.session_state.context, st.session_state.executor_model
                )

                # Update Execution Log display and store for the current step
                step_log = [
                    f"**Step {current_step['step_id']}**: {current_step['description']}",
                    f"🧠 **Reason:** {reasoning}",
                    f"🎬 **Act:** {action_str}",
                    f"👀 **Observe:**\n```\n{observation}\n```"
                ]
                st.session_state.execution_log = step_log

                # Store the reasoning and action in the step for later display
                current_step["reasoning"] = reasoning
                current_step["action_str"] = action_str

                # Debug output to verify reasoning is being updated
                log_debug(f"Reasoning for step {current_step['step_id']}: {reasoning}")

                # Update Plan State
                current_step["result"] = observation
                if "Error" in observation[:20] or "Error" in reasoning[:20]: # Basic error check
                    current_step["status"] = "Failed"
                    # Special handling: if this step was web_search, extract URLs from markdown result
                    if current_step.get("tool_suggestion") == "web_search" and isinstance(observation, str):
                        urls = extract_urls_from_markdown(observation)
                        st.session_state.context["search_result_urls"] = urls
                    st.session_state.messages.append({"role": "assistant", "content": f"Step {current_step['step_id']} failed. Stopping execution."})
                    st.session_state.current_step_index = -2 # Indicate failure halt
                else:
                    current_step["status"] = "Completed"
                    # Update context (simple way: store result by step_id)
                    st.session_state.context[f"step_{current_step['step_id']}_result"] = observation
                    st.session_state.current_step_index += 1

                st.rerun() # Rerun to process next step or completion

# --- Final Response Handling ---
elif st.session_state.plan is not None and st.session_state.current_step_index == len(st.session_state.plan) and len(st.session_state.plan) > 0:
    # Update status to show completion
    st.session_state.status_container.success("✅ Plan Execution Completed!")

    # Generate final response to the user
    def generate_final_response(client, user_query, plan):
        """Generates a final response to the user's query based on execution results."""
        if not client:
            return "I couldn't generate a proper response due to API configuration issues."

        # Prepare context for the final response
        results_summary = []

        # Extract references from web scraping and file reading steps
        references = []

        for step in plan:
            if step["result"] and step["status"] == "Completed":
                results_summary.append(f"Step {step['step_id']} ({step['description']}): {step['result']}")

                # Check if this step involves web scraping
                if step["tool_suggestion"] == "web_scrape" and "url" in step["description"].lower():
                    # Try to extract URL from the step description or result
                    url_match = re.search(r'https?://[^\s"\')]+', step["description"] + " " + str(step["result"]))
                    if url_match:
                        references.append(f"Web source: {url_match.group(0)}")

                # Check if this step involves web search
                elif step["tool_suggestion"] == "web_search":
                    # Web search results often contain URLs in the result
                    urls = re.findall(r'https?://[^\s"\')]+', str(step["result"]))
                    for url in urls:
                        references.append(f"Search result: {url}")

                # Check if this step involves reading files
                elif step["tool_suggestion"] == "read_file" and "filename" in str(step["description"]).lower():
                    # Try to extract filename from the step description or result
                    file_match = re.search(r'[\w\.-]+\.(txt|csv|json|md|py|html|xml|pdf)', step["description"] + " " + str(step["result"]))
                    if file_match:
                        references.append(f"File source: {file_match.group(0)}")

        # Remove duplicate references
        references = list(set(references))

        results_text = "\n\n".join(results_summary)
        references_text = "\n".join(references) if references else "No external sources were used."

        system_prompt = f"""You are a helpful assistant tasked with providing a thorough and insightful final response to the user's query.
The user asked: "{user_query}"

A plan was executed with the following results:
{results_text}

The following sources were used to gather information:
{references_text}

Based on these execution results, provide a comprehensive, thorough, and insightful response that directly answers the user's original query.
Focus on synthesizing the information, providing deep analysis, and presenting it in a user-friendly way.
If the execution results don't fully answer the query, acknowledge this and provide the best response possible with the available information.

Your summary should be detailed and demonstrate critical thinking about the information gathered.
Make connections between different pieces of information and highlight important insights.

IMPORTANT: If any web pages or files were used as sources, you MUST include references to these sources in your response.
Format the references section at the end of your response like this:

Sources:
- [Source description or title] (URL or filename)
"""

        try:
            completion = client.chat.completions.create(
                model=st.session_state.summarizer_model,  # Using the summarizer model for the final response
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please provide a final response to my query: {user_query}"}
                ],
                temperature=0.3
            )

            final_response = completion.choices[0].message.content
            return final_response
        except Exception as e:
            st.error(f"Error generating final response: {e}")
            return f"I've completed the steps to answer your query, but encountered an error when generating the final response. Here's a summary of what I found:\n\n{results_text}"

    # Generate the final response
    with st.spinner("Generating final response..."):
        # Find the last user message to use as the query
        user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
        if user_messages:
            user_query = user_messages[-1]["content"]
        else:
            user_query = "Unknown query"
        final_response = generate_final_response(client, user_query, st.session_state.plan)

        # Clear the status container after generating the response
        st.session_state.status_container.empty()

    # Process the final response to handle LaTeX and dollar amounts
    try:
        from processing.format_results import process_final_output
        processed_response = process_final_output(final_response)
    except ImportError:
        # If the module is not available, use the original response
        processed_response = final_response
        st.warning("LaTeX processing module not found. Dollar amounts may not display correctly.")

    # Add the processed response to the chat
    st.session_state.messages.append({"role": "assistant", "content": processed_response})

    # Add this new message to memory (automatically remembered by default)
    new_message_idx = len(st.session_state.messages) - 1
    update_message_memory(new_message_idx, True)

    # Display the processed response immediately
    with st.chat_message("assistant"):
        st.markdown(processed_response)

        # Add memory toggle for the new message
        cols = st.columns([6, 1])
        with cols[1]:
            # Create a toggle for memory inclusion
            new_state = st.toggle(
                "🧠",
                value=True,
                key=f"memory_toggle_{new_message_idx}",
                help="Toggle to include/exclude this message from memory"
            )

    # Automatically save the conversation
    filename, title = auto_save_conversation(st.session_state.messages, client, st.session_state.current_conversation_filename)
    st.session_state.current_conversation_filename = filename

    # Reset for next query
    st.session_state.current_step_index = -1
    # Keep plan visible, but could clear: st.session_state.plan = None

    # Transfer important information from context to persistent memory
    if st.session_state.context:
        # Copy any important results to persistent memory
        for key, value in st.session_state.context.items():
            if not key.startswith('step_'):
                # Only preserve named memory items, not step results
                st.session_state.persistent_memory[key] = value

    # Force a rerun to ensure the UI is updated
    st.rerun()
elif st.session_state.current_step_index == -2: # Halted due to failure
     # Update status to show failure
     st.session_state.status_container.error("❌ Plan Execution Halted due to step failure.")

     # Generate a failure response
     failed_step = next((step for step in st.session_state.plan if step["status"] == "Failed"), None)

     # Clear the status container after a short delay
     time.sleep(2)  # Keep the error message visible for 2 seconds
     st.session_state.status_container.empty()

     if failed_step:
         failure_message = f"I encountered an issue while trying to answer your query. The step '{failed_step['description']}' failed with the following error: {failed_step['result']}"

         # Add any successful steps' results
         successful_steps = [step for step in st.session_state.plan if step["status"] == "Completed"]

         # Extract references from successful steps
         references = []

         if successful_steps:
             failure_message += "\n\nHowever, I was able to complete the following steps:\n"

             for step in successful_steps:
                 failure_message += f"\n- {step['description']}: {step['result']}"

                 # Check if this step involves web scraping
                 if step["tool_suggestion"] == "web_scrape" and "url" in step["description"].lower():
                     # Try to extract URL from the step description or result
                     url_match = re.search(r'https?://[^\s"\')]+', step["description"] + " " + str(step["result"]))
                     if url_match:
                         references.append(f"Web source: {url_match.group(0)}")

                 # Check if this step involves web search
                 elif step["tool_suggestion"] == "web_search":
                     # Web search results often contain URLs in the result
                     urls = re.findall(r'https?://[^\s"\')]+', str(step["result"]))
                     for url in urls:
                         references.append(f"Search result: {url}")

                 # Check if this step involves reading files
                 elif step["tool_suggestion"] == "read_file" and "filename" in str(step["description"]).lower():
                     # Try to extract filename from the step description or result
                     file_match = re.search(r'[\w\.-]+\.(txt|csv|json|md|py|html|xml|pdf)', step["description"] + " " + str(step["result"]))
                     if file_match:
                         references.append(f"File source: {file_match.group(0)}")

         # Remove duplicate references
         references = list(set(references))

         # Add references to the failure message if any were found
         if references:
             failure_message += "\n\nSources used:\n"
             for ref in references:
                 failure_message += f"\n- {ref}"

         # Process the failure message to handle LaTeX and dollar amounts
         try:
             from processing.format_results import process_final_output
             processed_failure = process_final_output(failure_message)
         except ImportError:
             # If the module is not available, use the original message
             processed_failure = failure_message
             st.warning("LaTeX processing module not found. Dollar amounts may not display correctly.")

         st.session_state.messages.append({"role": "assistant", "content": processed_failure})

         # Add this new message to memory (automatically remembered by default)
         new_message_idx = len(st.session_state.messages) - 1
         update_message_memory(new_message_idx, True)

         # Display the processed failure message immediately
         with st.chat_message("assistant"):
             st.markdown(processed_failure)

             # Add memory toggle for the new message
             cols = st.columns([6, 1])
             with cols[1]:
                 # Create a toggle for memory inclusion
                 new_state = st.toggle(
                     "🧠",
                     value=True,
                     key=f"memory_toggle_{new_message_idx}",
                     help="Toggle to include/exclude this message from memory"
                 )

         # Automatically save the conversation
         filename, title = auto_save_conversation(st.session_state.messages, client, st.session_state.current_conversation_filename)
         st.session_state.current_conversation_filename = filename
     else:
         failure_message = "I encountered an issue while trying to answer your query. The execution plan failed, but I couldn't identify which specific step caused the problem."

         # Process the failure message to handle LaTeX and dollar amounts
         try:
             from processing.format_results import process_final_output
             processed_failure = process_final_output(failure_message)
         except ImportError:
             # If the module is not available, use the original message
             processed_failure = failure_message
             st.warning("LaTeX processing module not found. Dollar amounts may not display correctly.")

         st.session_state.messages.append({"role": "assistant", "content": processed_failure})

         # Add this new message to memory (automatically remembered by default)
         new_message_idx = len(st.session_state.messages) - 1
         update_message_memory(new_message_idx, True)

         # Display the processed failure message immediately
         with st.chat_message("assistant"):
             st.markdown(processed_failure)

             # Add memory toggle for the new message
             cols = st.columns([6, 1])
             with cols[1]:
                 # Create a toggle for memory inclusion
                 new_state = st.toggle(
                     "🧠",
                     value=True,
                     key=f"memory_toggle_{new_message_idx}",
                     help="Toggle to include/exclude this message from memory"
                 )

         # Automatically save the conversation
         filename, title = auto_save_conversation(st.session_state.messages, client, st.session_state.current_conversation_filename)
         st.session_state.current_conversation_filename = filename

     # Keep state as is for debugging, reset index to prevent re-execution attempt
     st.session_state.current_step_index = -1

     # Force a rerun to ensure the UI is updated
     st.rerun()


# Display Plan and Log
plan_display = []
if st.session_state.plan is not None and st.session_state.plan:
    for step in st.session_state.plan:
        status_icon = "⚪" # Pending
        if step["status"] == "Completed":
            status_icon = "✅"
        elif step["status"] == "Failed":
            status_icon = "❌"
        elif step["step_id"] == st.session_state.current_step_index + 1: # Next step to run
             status_icon = "⏳"

        # Hide dependency details from the user interface
        plan_display.append(f"{status_icon} **Step {step['step_id']}:** {step['description']}<br>")
        if step["status"] in ["Completed", "Failed"] and step["result"]:
             # Show result in collapsed section with the step description as the title
             with st.expander(f"   {step['description']}", expanded=False):
                  # Get the reasoning and action for this step
                  # Default values in case we can't find the specific reasoning/action
                  reasoning = step.get("reasoning", "No reasoning available")
                  action_str = step.get("action_str", "No action details available")
                  observation = str(step['result'])

                  # Display the reason, act, observe sections
                  st.markdown(f"🧠 **Reason:**")
                  st.markdown(reasoning)

                  st.markdown(f"🎬 **Act:**")
                  st.markdown(action_str)

                  st.markdown(f"👀 **Observe:**")
                  # Process the result to hide raw JSON
                  result_str = observation
                  # If result looks like JSON, try to format it more user-friendly
                  if (result_str.startswith('{') and result_str.endswith('}')) or \
                     (result_str.startswith('[') and result_str.endswith(']')):
                      try:
                          # Try to parse as JSON
                          result_obj = json.loads(result_str)
                          # If it's a simple error message in JSON, just show the message
                          if isinstance(result_obj, dict) and 'error' in result_obj:
                              st.error(result_obj['error'])
                          else:
                              # Otherwise show a cleaner version
                              st.json(result_obj)
                      except json.JSONDecodeError:
                          # If not valid JSON, show as code
                          st.code(result_str, language=None)
                  else:
                      st.code(result_str, language=None)


# Only display plan and log containers during execution, not in the final output
if st.session_state.current_step_index >= 0 and st.session_state.current_step_index < len(st.session_state.plan):
    # Show plan overview with progress
    total_steps = len(st.session_state.plan)
    current_step_num = st.session_state.current_step_index + 1
    progress_percentage = current_step_num / total_steps

    # Create a clean progress display with progress bar
    with plan_container.container():
        st.progress(progress_percentage)

        # Determine plan complexity for display
        complexity_level = "Simple"
        complexity_color = "green"
        if total_steps > 7:
            complexity_level = "Moderate"
            complexity_color = "orange"
        if total_steps > 12:
            complexity_level = "Complex"
            complexity_color = "red"

        # Show progress with complexity indicator
        st.caption(f"Processing: {int(progress_percentage * 100)}% complete ({current_step_num}/{total_steps} steps) - :{complexity_color}[{complexity_level} Plan]")

        # Add a detailed plan view in an expander
        with st.expander("View detailed plan", expanded=False):
            for i, step in enumerate(st.session_state.plan):
                status_icon = "⏳" if i == st.session_state.current_step_index else "✅" if i < st.session_state.current_step_index else "⏸️"
                deps = ", ".join([str(d) for d in step["dependencies"]]) if step["dependencies"] else "None"
                st.markdown(f"{status_icon} **Step {step['step_id']}**: {step['description']}\n   Tool: `{step['tool_suggestion']}` | Dependencies: `{deps}`")

    # Only show detailed execution log if debug mode is enabled
    if st.session_state.debug_mode:
        log_container.markdown("\n\n".join(st.session_state.execution_log), unsafe_allow_html=True)


# --- Chat Input ---
if prompt := st.chat_input("Enter your query..."):
    if not client:
        st.error("Please configure the OpenRouter API Key in the sidebar.")
    else:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Clear previous execution state
        st.session_state.plan = None
        st.session_state.current_step_index = -1

        # Transfer important information from context to persistent memory before clearing
        if st.session_state.context:
            # Copy any important results to persistent memory
            for key, value in st.session_state.context.items():
                if not key.startswith('step_'):
                    # Only preserve named memory items, not step results
                    st.session_state.persistent_memory[key] = value

        # Initialize context with persistent memory
        st.session_state.context = st.session_state.persistent_memory.copy()

        st.session_state.execution_log = []
        plan_container.empty() # Clear display immediately
        log_container.empty()

        # Check if this is a URL scraping request
        is_scrape_request, url, memory_key = detect_url_scrape_request(prompt)

        if is_scrape_request and url:
            # This is a direct URL scraping request, handle it without planning
            with st.spinner("🌐 Scraping website content..."):
                with st.chat_message("assistant"):
                    # Clear any previous status
                    st.session_state.status_container.empty()
                    # Show scraping status
                    st.session_state.status_container.info(f"🌐 Scraping content from {url}...")

                    # Use the web_scrape tool directly
                    from data_acquisition.news_scraper import WebScraper
                    try:
                        scraper = WebScraper()
                        content = scraper.scrape_content(url)

                        # Store the scraped content in memory
                        st.session_state.context[memory_key] = content
                        st.session_state.persistent_memory[memory_key] = content

                        # Create a response message
                        response = f"I've scraped the content from {url} and stored it in memory. I'll use this information to answer your future questions in this conversation.\n\nThe content includes information about: {content[:200]}...\n\nReference: {url}"

                        # Add to chat history
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.markdown(response)

                        # Update status
                        st.session_state.status_container.success(f"✅ Successfully scraped content from {url}")
                    except Exception as e:
                        error_msg = f"I encountered an error while trying to scrape {url}: {str(e)}"
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        st.error(error_msg)
        else:
            # Regular query - generate plan and execute
            with st.spinner("🤖 Planning..."):
                 with st.chat_message("assistant"):
                    # Clear any previous status
                    st.session_state.status_container.empty()
                    # Show planning status
                    st.session_state.status_container.info("🧠 Creating execution plan...")
                    # Assess query complexity first
                    query_complexity = assess_query_complexity(prompt)
                    if query_complexity == "High":
                        st.session_state.status_container.info("🧠 Complex query detected. Creating detailed plan...")

                    st.session_state.plan = run_planner(client, prompt, st.session_state.planner_model) or []
                    if st.session_state.plan:
                        # Update status with plan information and complexity
                        steps_count = len(st.session_state.plan)
                        complexity_emoji = "🟢" if steps_count < 8 else "🟡" if steps_count < 13 else "🔴"
                        st.session_state.status_container.success(f"✅ Plan created with {steps_count} steps {complexity_emoji}")
                        # Start execution
                        st.session_state.current_step_index = 0
                        st.rerun() # Trigger the execution loop
                    else:
                        st.error("Failed to generate a plan. Please check the console for errors.")
                        st.session_state.messages.append({"role": "assistant", "content": "Apologies, I encountered an issue while creating the execution plan. Please try again or check your API keys."})
