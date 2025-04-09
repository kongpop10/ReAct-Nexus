"""
Workspace sidebar component for the ReAct application.
Displays files in the workspace and allows opening them with system applications.
"""
import os
import streamlit as st
from config import WORKSPACE_DIR
from utils.file_system import open_file_with_system_app, get_file_icon

def render_workspace_sidebar():
    """Render the workspace sidebar with file explorer functionality."""
    st.sidebar.subheader("📂 Workspace")
    
    # Initialize session state for current directory if not exists
    if "current_directory" not in st.session_state:
        st.session_state.current_directory = ""
    
    # Get the current directory path (relative to workspace)
    current_dir = st.session_state.current_directory
    
    # Calculate the full path
    if current_dir:
        full_path = os.path.join(WORKSPACE_DIR, current_dir)
    else:
        full_path = WORKSPACE_DIR
    
    # Show current path with navigation
    if current_dir:
        # Show breadcrumb navigation
        path_parts = current_dir.split(os.path.sep)
        breadcrumb = "📂 "
        
        # Add root directory with link
        if st.sidebar.button("📁 Root", key="nav_root"):
            st.session_state.current_directory = ""
            st.rerun()
        
        # Add intermediate directories with links
        for i, part in enumerate(path_parts[:-1]):
            path_to_here = os.path.sep.join(path_parts[:i+1])
            if st.sidebar.button(f"📁 {part}", key=f"nav_{path_to_here}"):
                st.session_state.current_directory = path_to_here
                st.rerun()
            breadcrumb += f"{part} / "
        
        # Add current directory (without link)
        breadcrumb += path_parts[-1]
        st.sidebar.markdown(f"**Current: {breadcrumb}**")
    else:
        st.sidebar.markdown("**Current: 📁 Root**")
    
    # Check if directory exists
    if not os.path.exists(full_path):
        st.sidebar.error(f"Directory not found: {full_path}")
        return
    
    # List directories and files
    try:
        items = os.listdir(full_path)
        
        # Separate directories and files
        directories = []
        files = []
        
        for item in items:
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                directories.append(item)
            else:
                files.append(item)
        
        # Sort directories and files alphabetically
        directories.sort()
        files.sort()
        
        # Display directories first
        if directories:
            st.sidebar.markdown("### 📁 Directories")
            for directory in directories:
                # Create a button for each directory
                if st.sidebar.button(f"📁 {directory}", key=f"dir_{directory}"):
                    # Navigate to this directory
                    if current_dir:
                        st.session_state.current_directory = os.path.join(current_dir, directory)
                    else:
                        st.session_state.current_directory = directory
                    st.rerun()
        
        # Display files
        if files:
            st.sidebar.markdown("### 📄 Files")
            for file in files:
                # Get appropriate icon for the file
                icon = get_file_icon(file)
                
                # Create a button for each file
                if st.sidebar.button(f"{icon} {file}", key=f"file_{file}"):
                    # Open the file with system application
                    file_path = os.path.join(current_dir, file) if current_dir else file
                    result = open_file_with_system_app(file_path)
                    
                    # Show success or error message
                    if result.startswith("Error"):
                        st.sidebar.error(result)
                    else:
                        st.sidebar.success(result)
        
        # Show message if directory is empty
        if not directories and not files:
            st.sidebar.info("This directory is empty.")
            
    except Exception as e:
        st.sidebar.error(f"Error accessing directory: {e}")
