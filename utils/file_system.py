"""
File system utilities for the ReAct application.
Includes functions for opening files with system applications.
"""
import os
import platform
import subprocess
import streamlit as st
from config import WORKSPACE_DIR

def get_absolute_path(filename, workspace_dir=WORKSPACE_DIR):
    """
    Get the absolute path for a file in the workspace directory.
    
    Args:
        filename (str): The name of the file or relative path within the workspace
        workspace_dir (str): The workspace directory (default: WORKSPACE_DIR from config)
        
    Returns:
        str: The absolute path to the file
    """
    # Handle both absolute paths and relative paths within the workspace
    if os.path.isabs(filename):
        return filename
    else:
        return os.path.join(workspace_dir, filename)

def open_file_with_system_app(filename):
    """
    Open a file with the default system application based on the operating system.
    
    Args:
        filename (str): The name of the file or relative path within the workspace
        
    Returns:
        str: A message indicating the result of the operation
    """
    filepath = get_absolute_path(filename)
    
    if not os.path.exists(filepath):
        return f"Error: File '{filename}' not found in workspace."
    
    try:
        system = platform.system()
        
        if system == 'Windows':
            # On Windows, use the built-in os.startfile
            os.startfile(filepath)
        elif system == 'Darwin':  # macOS
            # On macOS, use the 'open' command
            subprocess.run(['open', filepath], check=True)
        else:  # Linux and other Unix-like systems
            # On Linux, use 'xdg-open'
            subprocess.run(['xdg-open', filepath], check=True)
            
        return f"Successfully opened '{filename}' with the default application."
    except Exception as e:
        return f"Error opening file '{filename}': {e}"

def get_file_icon(filename):
    """
    Get an appropriate icon for a file based on its extension.
    
    Args:
        filename (str): The name of the file
        
    Returns:
        str: An emoji icon representing the file type
    """
    # Get the file extension (lowercase)
    _, ext = os.path.splitext(filename.lower())
    
    # Map extensions to icons
    if ext == '':
        return '📄'  # Generic file icon for files with no extension
    elif ext == '.md':
        return '📝'  # Markdown files
    elif ext == '.py':
        return '🐍'  # Python files
    elif ext == '.json':
        return '🔄'  # JSON files
    elif ext == '.txt':
        return '📄'  # Text files
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
        return '🖼️'  # Image files
    elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
        return '🎵'  # Audio files
    elif ext in ['.mp4', '.avi', '.mov', '.wmv']:
        return '🎬'  # Video files
    elif ext in ['.pdf']:
        return '📑'  # PDF files
    elif ext in ['.doc', '.docx']:
        return '📘'  # Word documents
    elif ext in ['.xls', '.xlsx']:
        return '📊'  # Excel spreadsheets
    elif ext in ['.ppt', '.pptx']:
        return '📽️'  # PowerPoint presentations
    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
        return '🗜️'  # Archive files
    else:
        return '📄'  # Default file icon
