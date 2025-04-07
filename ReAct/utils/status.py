"""
Status update utilities for the ReAct application.
"""
import streamlit as st

def log_debug(message):
    """Log debug information only if debug mode is enabled"""
    if st.session_state.debug_mode:
        st.write(message)

def update_tool_status(tool_name, **kwargs):
    """Update the status display with tool execution information"""
    # Always update the status indicator
    if 'status_container' in st.session_state and st.session_state.status_container is not None:
        params = ', '.join([f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in kwargs.items()])
        st.session_state.status_container.info(f"🔧 Using tool: {tool_name}({params})")
    # Log detailed information if debug mode is on
    if st.session_state.debug_mode:
        st.write(f"TOOL: {tool_name}({', '.join([f'{k}={v!r}' for k, v in kwargs.items()])})")
