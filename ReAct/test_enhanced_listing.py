"""
Test script for the enhanced file listing functionality.
"""
import os
import sys
import streamlit as st

# Mock Streamlit session state for testing
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# Import after setting up mock session state
from tools.enhanced_file_tools import enhanced_list_files

def format_directory_listing(directory=None):
    """Format directory listing in a user-friendly way."""
    # Get the target directory
    from config import WORKSPACE_DIR
    if directory:
        if os.path.isabs(directory):
            target_dir = directory
        else:
            target_dir = os.path.join(WORKSPACE_DIR, directory)
    else:
        target_dir = WORKSPACE_DIR

    # Check if directory exists
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

def main():
    """Test the enhanced file listing function."""
    print("Testing enhanced file listing...\n")

    # Test our direct implementation
    print("Using direct implementation:\n")
    result = format_directory_listing()
    print(result)

    # Try the enhanced_list_files function if it works
    try:
        print("\nUsing enhanced_list_files function:\n")
        result = enhanced_list_files()
        print(result)
    except Exception as e:
        print(f"Error using enhanced_list_files: {e}")

if __name__ == "__main__":
    main()
