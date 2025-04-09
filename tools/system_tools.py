"""
System-related tools for the ReAct application.
Includes functions for interacting with the operating system.
"""
import streamlit as st
from utils.file_system import open_file_with_system_app
from utils.status import update_tool_status

def open_file(filename: str) -> str:
    """
    Opens a file from the workspace with the default system application.
    
    Args:
        filename: The name of the file to open
        
    Returns:
        str: A message indicating the result of the operation
    """
    update_tool_status("open_file", filename=filename)
    return open_file_with_system_app(filename)
