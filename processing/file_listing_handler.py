"""
File listing handler for the ReAct application.
Provides enhanced file listing with categorization and icons.
"""
import os
from config import WORKSPACE_DIR

def format_directory_listing(directory=None):
    """Format directory listing in a user-friendly way.
    
    Args:
        directory: Optional subdirectory within the workspace to list files from
        
    Returns:
        str: Formatted markdown string with categorized file listing
    """
    # Get the target directory
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

def process_file_listing_response(response):
    """Process a file listing response to make it more user-friendly.
    
    Args:
        response (str): The original file listing response
        
    Returns:
        str: Formatted markdown string with categorized file listing
    """
    # Check if this is a file listing response
    if not response or not isinstance(response, str):
        return response
    
    # If the response is just a list of files (one per line), convert it to enhanced format
    lines = response.strip().split('\n')
    
    # Simple heuristic to detect if this is a file listing:
    # - More than 1 line
    # - No lines contain special characters like : or = (which would indicate it's not just filenames)
    # - No lines are longer than 100 characters (typical for filenames)
    if len(lines) > 1 and all(len(line) < 100 and ':' not in line and '=' not in line for line in lines):
        # This looks like a simple file listing, let's enhance it
        
        # Categorize files
        directories = []
        markdown_files = []
        python_files = []
        json_files = []
        text_files = []
        other_files = []
        
        for item in lines:
            item = item.strip()
            if not item:
                continue
                
            # Try to determine if it's a directory (this is a best guess since we only have names)
            if '.' not in item or item.endswith('/') or item.endswith('\\'):
                directories.append(item.rstrip('/\\'))
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
        result = "# Files in workspace\n\n"
        
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
    
    # If it doesn't look like a simple file listing, return the original response
    return response
