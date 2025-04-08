"""
Enhanced file operation tools for the ReAct application.
Provides improved file listing with categorization and icons.
"""
import os
import streamlit as st
from config import WORKSPACE_DIR
from utils.status import update_tool_status

def enhanced_list_files(directory: str = None) -> str:
    """Lists files in the workspace directory or a subdirectory with improved formatting.
    
    Files are categorized by type and displayed with appropriate icons.

    Args:
        directory: Optional subdirectory within the workspace to list files from
        
    Returns:
        str: Formatted markdown string with categorized file listing
    """
    if directory:
        update_tool_status("enhanced_list_files", directory=directory)
        # Handle both absolute paths and relative paths within the workspace
        if os.path.isabs(directory):
            target_dir = directory
        else:
            target_dir = os.path.join(WORKSPACE_DIR, directory)
    else:
        update_tool_status("enhanced_list_files")
        target_dir = WORKSPACE_DIR

    try:
        if not os.path.exists(target_dir):
            return f"Error: Directory '{target_dir}' not found."
        if not os.path.isdir(target_dir):
            return f"Error: '{target_dir}' is not a directory."

        # Get all files and directories
        all_items = os.listdir(target_dir)
        if not all_items:
            return f"Directory '{target_dir}' is empty."
        
        # Categorize items
        directories = []
        markdown_files = []
        python_files = []
        json_files = []
        text_files = []
        other_files = []
        
        for item in all_items:
            item_path = os.path.join(target_dir, item)
            
            if os.path.isdir(item_path):
                directories.append(item)
            elif item.endswith('.md'):
                markdown_files.append(item)
            elif item.endswith('.py'):
                python_files.append(item)
            elif item.endswith('.json'):
                json_files.append(item)
            elif item.endswith('.txt'):
                text_files.append(item)
            else:
                other_files.append(item)
        
        # Format the output
        result = f"# Files in {os.path.basename(target_dir) or 'workspace'}\n\n"
        
        # Add directories
        if directories:
            result += "## 📁 Directories\n\n"
            for directory in sorted(directories):
                result += f"- 📁 `{directory}`\n"
            result += "\n"
        
        # Add markdown files
        if markdown_files:
            result += "## 📝 Markdown Files\n\n"
            for file in sorted(markdown_files):
                result += f"- 📝 `{file}`\n"
            result += "\n"
        
        # Add python files
        if python_files:
            result += "## 🐍 Python Files\n\n"
            for file in sorted(python_files):
                result += f"- 🐍 `{file}`\n"
            result += "\n"
        
        # Add JSON files
        if json_files:
            result += "## 🔄 JSON Files\n\n"
            for file in sorted(json_files):
                result += f"- 🔄 `{file}`\n"
            result += "\n"
        
        # Add text files
        if text_files:
            result += "## 📄 Text Files\n\n"
            for file in sorted(text_files):
                result += f"- 📄 `{file}`\n"
            result += "\n"
        
        # Add other files
        if other_files:
            result += "## 📎 Other Files\n\n"
            for file in sorted(other_files):
                result += f"- 📎 `{file}`\n"
            result += "\n"
        
        return result
    except Exception as e:
        return f"Error listing files: {e}"
