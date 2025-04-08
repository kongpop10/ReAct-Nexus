"""
Python execution tools for the ReAct application.
"""
import io
import contextlib
import traceback
import streamlit as st
from utils.status import update_tool_status

def reset_python_environment() -> str:
    """
    Resets the Python execution environment by clearing all stored variables.
    """
    if "python_exec_vars" in st.session_state:
        st.session_state.python_exec_vars = {}
    return "Python execution environment has been reset. All variables have been cleared."


def list_python_variables() -> str:
    """
    Lists all variables currently stored in the Python execution environment.
    """
    if "python_exec_vars" not in st.session_state or not st.session_state.python_exec_vars:
        return "No variables are currently stored in the Python execution environment."

    result = "Current Python environment variables:\n"
    for var_name, var_value in st.session_state.python_exec_vars.items():
        # Skip internal variables and functions
        if var_name.startswith('__') or callable(var_value):
            continue

        # Format the value based on its type
        if isinstance(var_value, (list, tuple)) and len(var_value) > 10:
            value_str = f"{type(var_value).__name__} with {len(var_value)} items"
        elif isinstance(var_value, dict) and len(var_value) > 10:
            value_str = f"dict with {len(var_value)} keys"
        elif isinstance(var_value, str) and len(var_value) > 100:
            value_str = f"'{var_value[:97]}...'"
        else:
            value_str = str(var_value)

        result += f"- {var_name}: {value_str}\n"

    return result


def execute_python(code: str, reset: bool = False) -> str:
    """
    Executes a Python code snippet.
    !!! DANGER ZONE: This uses exec() and is NOT secure. For demo only. !!!
    Requires a secure sandboxed environment for production.

    Args:
        code: The Python code to execute
        reset: If True, resets the environment before execution (default: False)
    """
    st.warning("**Security Warning:** Executing Python code dynamically. Ensure code is safe! (Using `exec`)")
    update_tool_status("execute_python")
    st.code(code, language='python')

    # Reset environment if requested
    if reset:
        reset_python_environment()

    # Initialize persistent local variables in session state if not already present
    if "python_exec_vars" not in st.session_state:
        st.session_state.python_exec_vars = {}

    # Use the persistent variables from session state
    local_vars = st.session_state.python_exec_vars
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(code, globals(), local_vars)

        # Save the updated variables back to session state
        st.session_state.python_exec_vars = local_vars

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
