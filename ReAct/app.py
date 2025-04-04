import streamlit as st
import os
import json
import re
from datetime import datetime

def generate_title(messages, client=None):
    """Generate a title based on the conversation messages using Gemini model."""
    try:
        # Extract the user's query from messages
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]

        # If we have user messages and a client, use Gemini to generate a title
        if user_messages and client:
            # Combine up to the last 3 user messages for context
            context = "\n".join(user_messages[-3:])

            # Use the Gemini model to generate a title
            try:
                completion = client.chat.completions.create(
                    model="google/gemini-2.0-flash-exp:free",
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
import time
import random

# --- Configuration & Constants ---
load_dotenv() # Load .env file if it exists
WORKSPACE_DIR = "agent_workspace"
if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)

# --- Tool Implementations ---

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

        # Format results in markdown
        return process_search_results(results_json)
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})

def web_scrape(url: str = None, urls: str = None) -> str:
    """Scrapes the text content of a given URL or list of URLs using WebScraper class."""
    # Handle both parameter names (url and urls) for backward compatibility
    target_url = url if url is not None else urls
    st.write(f"TOOL: web_scrape(url='{target_url}')")

    if target_url is None:
        return "Error: No URL provided. Please provide a URL using the 'url' parameter."

    from agent_workspace.news_scraper import WebScraper

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
    st.write(f"TOOL: read_file(filename='{filename}')")
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

    st.write(f"TOOL: write_file(filename='{filename}', content='...', append={append})")
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
        st.write(f"TOOL: list_files(directory='{directory}')")
        # Handle both absolute paths and relative paths within the workspace
        if os.path.isabs(directory):
            target_dir = directory
        else:
            target_dir = os.path.join(WORKSPACE_DIR, directory)
    else:
        st.write("TOOL: list_files()")
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
    st.write(f"TOOL: delete_file(filename='{filename}')")
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


def execute_python(code: str) -> str:
    """
    Executes a Python code snippet.
    !!! DANGER ZONE: This uses exec() and is NOT secure. For demo only. !!!
    Requires a secure sandboxed environment for production.
    """
    st.warning("**Security Warning:** Executing Python code dynamically. Ensure code is safe! (Using `exec`)")
    st.write(f"TOOL: execute_python(code=...)")
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

    st.write(f"TOOL: get_stock_data(symbol='{actual_symbol}')")

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

TOOLS = {
    "web_search": web_search,
    "web_scrape": web_scrape,
    "get_stock_data": get_stock_data,
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "delete_file": delete_file,
    "execute_python": execute_python,
    # "short_term_memory_get": lambda key: st.session_state.context.get(key, None), # Example how memory could be a tool
    # "short_term_memory_set": lambda key, value: st.session_state.context.update({key: value}),
}

TOOL_DESCRIPTIONS = """
Available Tools:
- web_search(query: str): Searches the web for the given query. Returns a list of search results (title, url, snippet).
- web_scrape(url: str): Fetches and extracts the main text content from a given URL or list of URLs. Returns the text content or a JSON object with URLs as keys and content as values.
- get_stock_data(symbol: str) or get_stock_data(ticker: str) or get_stock_data(stock_symbol: str): Fetches real-time stock data for the given stock symbol using Alpha Vantage API. Returns stock information in JSON format.
- read_file(filename: str): Reads the content of the specified file from the workspace. Returns the file content.
- write_file(filename: str, content: str, append: bool = False) or write_file(filename: str, text: str, append: bool = False): Writes or appends the given content to the specified file in the workspace. Accepts either 'content' or 'text' parameter. If append=True, adds to the existing file; if append=False (default), overwrites the file. Returns a success or error message.
- list_files(directory: str = None): Lists all files in the workspace directory or a specified subdirectory. Returns a list of filenames.
- delete_file(filename: str): Deletes the specified file from the workspace directory. Returns a success or error message.
- execute_python(code: str): Executes the provided Python code snippet. Can be used for calculations, data manipulation, etc. Returns the output/result or error. Use standard libraries (os, json, requests, etc. are available). Print statements will be captured as output. !!! CAUTION: Security risk if code is not controlled !!!
"""

# --- LLM Interaction ---

def get_openai_client(api_key, base_url="https://openrouter.ai/api/v1"):
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=base_url)

def run_planner(client: OpenAI, user_query: str, planner_model: str) -> list:
    """Generates the initial plan using the Planner LLM. Always returns a list."""
    if not client:
        st.error("API key not configured. Cannot run Planner.")
        return []

    system_prompt = f"""You are a meticulous planning agent. Your task is to break down the user's query into a sequence of actionable steps.
Today's Date: {datetime.now().strftime('%Y-%m-%d')}
You have access to the following tools:
{TOOL_DESCRIPTIONS}

**IMPORTANT FOR FILE OPERATIONS:**
- When the user wants to ADD, APPEND, or UPDATE content in an existing file, plan to use `write_file` with `append=true`
- When the user wants to CREATE a new file or REPLACE/OVERWRITE an existing file, plan to use `write_file` with `append=false` (default)
- When the user wants to DELETE or REMOVE a file, plan to use `delete_file` with the filename
- Examples where `append=true` is needed: "add a line to file.txt", "append text to file.txt", "update file.txt with new content"
- Examples where `delete_file` is needed: "delete file.txt", "remove file.txt", "erase file.txt"

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
            temperature=0.2,
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

        # Validate plan structure
        for i, step in enumerate(plan_list):
            if not all(k in step for k in ["step_id", "description", "tool_suggestion", "dependencies", "status", "result"]):
                raise ValueError(f"Step {i+1} is missing required keys.")
            step["step_id"] = i + 1 # Ensure step_ids are sequential 1, 2, 3...
            step["status"] = "Pending" # Ensure initial status
            step["result"] = None     # Ensure initial result
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

   **IMPORTANT FOR FILE OPERATIONS:**
   - When the user wants to ADD, APPEND, or UPDATE content in an existing file, use `write_file` with `append=true`
   - When the user wants to CREATE a new file or REPLACE/OVERWRITE an existing file, use `write_file` with `append=false` (default)
   - When the user wants to DELETE or REMOVE a file, use `delete_file` with the filename
   - Examples where `append=true` is needed: "add a line to file.txt", "append text to file.txt", "update file.txt with new content"
   - Examples where `delete_file` is needed: "delete file.txt", "remove file.txt", "erase file.txt"

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
        st.write(f"Attempting LLM call for step: {step_desc}") # Debug output
        completion = client.chat.completions.create(
            model=executor_model,
            messages=[
                {"role": "system", "content": reasoning_prompt},
                {"role": "user", "content": f"Execute step: {step_desc}"}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        st.write(f"LLM call completed. Completion object: {completion}") # Debug output

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
        st.write(f"Raw action JSON: {action_json_str}") # Debug output

        # Extract reasoning from the LLM response
        # The LLM should be thinking about the reasoning in its internal process
        # before generating the action JSON, so we'll consider the content as containing
        # the reasoning implicitly

        # Parse action JSON
        try:
            action = json.loads(action_json_str)

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

                st.write(f"\n\nAttempting to execute: {action['tool']} with args {tool_args}")

                if action['tool'] not in TOOLS:
                    raise ValueError(f"Tool '{action['tool']}' not registered in TOOLS dictionary")

                tool_func = TOOLS[action['tool']]

                # Validate arguments are in keyword form
                if not isinstance(tool_args, dict):
                    raise TypeError(f"Tool arguments must be dictionary, got {type(tool_args).__name__}")

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
st.caption(f"Timestamp: {datetime.now().isoformat()}")
st.markdown("---")

# --- Configuration Sidebar ---
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

page = st.sidebar.radio("Sidebar Pages", ["Configuration", "Conversation Management"], index=0)

if page == "Configuration":
    st.sidebar.title("Configuration")
    st.session_state.api_key = st.sidebar.text_input("OpenRouter API Key", type="password", value=st.session_state.api_key)
    st.session_state.base_url = st.sidebar.text_input("OpenRouter API Base", value=st.session_state.base_url)
    st.session_state.planner_model = st.sidebar.text_input("Planner Model", value=st.session_state.planner_model)
    st.session_state.executor_model = st.sidebar.text_input("Executor Model", value=st.session_state.executor_model)
    st.session_state.summarizer_model = st.sidebar.text_input("Summarizer Model", value=st.session_state.summarizer_model)
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

    saved_successfully = False
    saved_filename = ""

    with st.sidebar.expander("💾 Save Conversation", expanded=True):
        save_clicked = st.button("💾 Save Conversation", type="primary", use_container_width=True)

        if save_clicked and len(st.session_state.messages) > 0:
            try:
                # Generate title using Gemini model
                generated_title = generate_title(st.session_state.messages, client)

                # Create filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"conversation_{timestamp}.json"
                created_at = datetime.now().isoformat()

                # Save conversation with metadata
                save_conversation(filename, st.session_state.messages, title=generated_title, created_at=created_at)

                saved_successfully = True
                saved_filename = filename

                st.success(f"Conversation saved as: {generated_title}")

                # Provide download option
                conv_dir = os.path.join(WORKSPACE_DIR, 'agent_workspace')
                filepath = os.path.join(conv_dir, filename)
                with open(filepath, "rb") as f:
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=f,
                        file_name=filename,
                        mime="application/json",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Failed to save conversation: {e}")
        elif save_clicked and len(st.session_state.messages) == 0:
            st.warning("No conversation to save. Start a chat first.")

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
                 on_click=lambda: st.session_state.update({'messages': []}),
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
if "execution_log" not in st.session_state:
    st.session_state.execution_log = [] # To show Reason/Act/Observe

# Display chat messages with modern styling
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Display message content directly without custom styling div
        st.markdown(message['content'])

# Layout for Plan and Execution Log
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 Current Plan")
    st.markdown("<style>.stExpander {border: none !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1);}</style>", unsafe_allow_html=True)
    plan_container = st.empty()

with col2:
    st.subheader("⚙️ Execution")
    log_container = st.empty()

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
            st.status(f"Executing Step {current_step['step_id']}: {current_step['description']}...")
            with st.spinner(f"Running Step {current_step['step_id']}..."):
                reasoning, action_str, observation = run_executor_step(
                    client, current_step, st.session_state.context, st.session_state.executor_model
                )

                # Update Execution Log display
                st.session_state.execution_log = [
                    f"**Step {current_step['step_id']}**: {current_step['description']}",
                    f"🧠 **Reason:** {reasoning}",
                    f"🎬 **Act:** {action_str}",
                    f"👀 **Observe:**\n```\n{observation}\n```"
                ]

                # Debug output to verify reasoning is being updated
                st.write(f"Reasoning for step {current_step['step_id']}: {reasoning}")

                # Update Plan State
                current_step["result"] = observation
                if "Error" in observation[:20] or "Error" in reasoning[:20]: # Basic error check
                    current_step["status"] = "Failed"
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
    st.success("✅ Plan Execution Completed!")

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
        final_response = generate_final_response(client, st.session_state.messages[-2]["content"], st.session_state.plan)

    # Process the final response to handle LaTeX and dollar amounts
    try:
        from agent_workspace.format_results import process_final_output
        processed_response = process_final_output(final_response)
    except ImportError:
        # If the module is not available, use the original response
        processed_response = final_response
        st.warning("LaTeX processing module not found. Dollar amounts may not display correctly.")

    # Add the processed response to the chat
    st.session_state.messages.append({"role": "assistant", "content": processed_response})

    # Display the processed response immediately
    with st.chat_message("assistant"):
        st.markdown(processed_response)

    # Reset for next query
    st.session_state.current_step_index = -1
    # Keep plan visible, but could clear: st.session_state.plan = None
    # st.session_state.context = {} # Optionally clear context

    # Force a rerun to ensure the UI is updated
    st.rerun()
elif st.session_state.current_step_index == -2: # Halted due to failure
     st.error("❌ Plan Execution Halted due to step failure.")

     # Generate a failure response
     failed_step = next((step for step in st.session_state.plan if step["status"] == "Failed"), None)
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
             from agent_workspace.format_results import process_final_output
             processed_failure = process_final_output(failure_message)
         except ImportError:
             # If the module is not available, use the original message
             processed_failure = failure_message
             st.warning("LaTeX processing module not found. Dollar amounts may not display correctly.")

         st.session_state.messages.append({"role": "assistant", "content": processed_failure})

         # Display the processed failure message immediately
         with st.chat_message("assistant"):
             st.markdown(processed_failure)
     else:
         failure_message = "I encountered an issue while trying to answer your query. The execution plan failed, but I couldn't identify which specific step caused the problem."

         # Process the failure message to handle LaTeX and dollar amounts
         try:
             from agent_workspace.format_results import process_final_output
             processed_failure = process_final_output(failure_message)
         except ImportError:
             # If the module is not available, use the original message
             processed_failure = failure_message
             st.warning("LaTeX processing module not found. Dollar amounts may not display correctly.")

         st.session_state.messages.append({"role": "assistant", "content": processed_failure})

         # Display the processed failure message immediately
         with st.chat_message("assistant"):
             st.markdown(processed_failure)

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
             # Show result in collapsed section, but hide raw JSON
             with st.expander(f"   Result (Step {step['step_id']})", expanded=False):
                  # Process the result to hide raw JSON
                  result_str = str(step['result'])
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


plan_container.markdown("\n".join(plan_display), unsafe_allow_html=True)
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
        st.session_state.context = {}
        st.session_state.execution_log = []
        plan_container.empty() # Clear display immediately
        log_container.empty()

        # Generate Plan
        with st.spinner("🤖 Planning..."):
             with st.chat_message("assistant"):
                st.session_state.plan = run_planner(client, prompt, st.session_state.planner_model) or []
                if st.session_state.plan:
                    st.success("Plan generated successfully!")
                    st.session_state.messages.append({"role": "assistant", "content": f"I've created a plan with {len(st.session_state.plan)} steps to solve your request."})
                    st.session_state.current_step_index = 0 # Start execution
                    st.rerun() # Trigger the execution loop
                else:
                    st.error("Failed to generate a plan. Please check the console for errors.")
                    st.session_state.messages.append({"role": "assistant", "content": "Apologies, I encountered an issue while creating the execution plan. Please try again or check your API keys."})
