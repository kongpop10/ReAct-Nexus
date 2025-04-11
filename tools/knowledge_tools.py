"""
Knowledge base tools for the ReAct application.
Includes adding, retrieving, listing, and deleting knowledge entries.
"""
import os
import streamlit as st
from data_acquisition.news_scraper import WebScraper
from utils.status import update_tool_status
from config import WORKSPACE_DIR

# This will be initialized in app.py and passed to the tools
knowledge_manager = None

def kb_add_web(url: str, title: str = None) -> str:
    """Adds a web page to the knowledge base."""
    update_tool_status("kb_add_web", url=url, title=title)

    # First scrape the content
    try:
        scraper = WebScraper()
        content = scraper.scrape_content(url)

        # Add to knowledge base
        entry = knowledge_manager.add_web_source(url, content, title)

        if "error" in entry:
            return f"Error adding to knowledge base: {entry['error']}"

        # Add to session memory
        st.session_state.context[entry["memory_key"]] = content
        st.session_state.persistent_memory[entry["memory_key"]] = content

        return f"Successfully added web content to knowledge base with ID: {entry['id']} and memory key: {entry['memory_key']}"
    except Exception as e:
        return f"Failed to add web content to knowledge base: {str(e)}"

def kb_add_file(filename: str, title: str = None) -> str:
    """Adds a local markdown file to the knowledge base."""
    update_tool_status("kb_add_file", filename=filename, title=title)

    filepath = os.path.join(WORKSPACE_DIR, filename)

    try:
        # Add to knowledge base
        entry = knowledge_manager.add_local_source(filepath, title)

        if "error" in entry:
            return f"Error adding to knowledge base: {entry['error']}"

        # Get content and add to session memory
        content = knowledge_manager.get_entry_content(entry["id"])
        st.session_state.context[entry["memory_key"]] = content
        st.session_state.persistent_memory[entry["memory_key"]] = content

        return f"Successfully added file to knowledge base with ID: {entry['id']} and memory key: {entry['memory_key']}"
    except Exception as e:
        return f"Failed to add file to knowledge base: {str(e)}"

def kb_list() -> str:
    """Lists all entries in the knowledge base."""
    update_tool_status("kb_list")

    try:
        entries = knowledge_manager.get_all_entries()
        if not entries:
            return "Knowledge base is empty."

        result = "Knowledge Base Entries:\n\n"
        for entry in entries:
            status_icon = "🟢" if entry["status"] == "active" else "⚪"
            entry_type = "Web Source" if entry["type"] == "web" else "Local File"
            result += f"{status_icon} **{entry['title']}** ({entry_type})\n"
            result += f"  ID: {entry['id']}\n"
            result += f"  Memory Key: {entry['memory_key']}\n"
            result += f"  Source: {entry['source']}\n"
            result += f"  Added: {entry['added_date']}\n\n"

        return result
    except Exception as e:
        return f"Error listing knowledge base entries: {str(e)}"

def kb_get(entry_id: str = None, memory_key: str = None, **kwargs) -> str:
    """Gets the content of a knowledge base entry by ID or memory key."""
    # Handle potential numeric keys or positional arguments
    if not entry_id and not memory_key:
        # Check if there are numeric keys in kwargs (from LLM responses)
        for k, v in kwargs.items():
            try:
                # If the key is a numeric string or can be converted to int
                int(k)
                # Use the first value found as entry_id
                if isinstance(v, str) and v.strip():
                    entry_id = v
                    break
            except (ValueError, TypeError):
                continue

    # Log what we're actually using
    update_tool_status("kb_get", entry_id=entry_id, memory_key=memory_key)

    if not entry_id and not memory_key:
        return "Error: Either entry_id or memory_key must be provided."

    try:
        if entry_id:
            entry = knowledge_manager.get_entry_by_id(entry_id)
            if not entry:
                return f"Error: Entry with ID {entry_id} not found."
            content = knowledge_manager.get_entry_content(entry_id)
        else:  # memory_key
            entry = knowledge_manager.get_entry_by_memory_key(memory_key)
            if not entry:
                return f"Error: Entry with memory key {memory_key} not found."
            content = knowledge_manager.get_entry_content(entry["id"])

        return content
    except Exception as e:
        return f"Error retrieving knowledge base entry: {str(e)}"

def kb_delete(entry_id: str) -> str:
    """Deletes an entry from the knowledge base."""
    update_tool_status("kb_delete", entry_id=entry_id)

    try:
        entry = knowledge_manager.get_entry_by_id(entry_id)
        if not entry:
            return f"Error: Entry with ID {entry_id} not found."

        # Remove from memory if present
        memory_key = entry["memory_key"]
        if memory_key in st.session_state.context:
            del st.session_state.context[memory_key]
        if memory_key in st.session_state.persistent_memory:
            del st.session_state.persistent_memory[memory_key]

        # Delete from knowledge base
        result = knowledge_manager.delete_entry(entry_id)
        if "error" in result:
            return f"Error deleting entry: {result['error']}"

        return f"Successfully deleted entry {entry_id} from knowledge base."
    except Exception as e:
        return f"Error deleting knowledge base entry: {str(e)}"

def kb_search(query: str) -> str:
    """Searches the knowledge base for entries matching the query."""
    update_tool_status("kb_search", query=query)

    try:
        entries = knowledge_manager.search_entries(query)
        if not entries:
            return f"No entries found matching query: {query}"

        result = f"Search Results for '{query}':\n\n"
        for entry in entries:
            status_icon = "🟢" if entry["status"] == "active" else "⚪"
            entry_type = "Web Source" if entry["type"] == "web" else "Local File"
            result += f"{status_icon} {entry['title']} ({entry_type})\n"
            result += f"  ID: {entry['id']}\n"
            result += f"  Memory Key: {entry['memory_key']}\n"
            result += f"  Source: {entry['source']}\n\n"

        return result
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"
