"""
File operation tools for the ReAct application.
Includes reading, writing, listing, and deleting files.
"""
import os
import streamlit as st
from config import WORKSPACE_DIR
from utils.status import update_tool_status

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
