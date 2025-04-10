"""
ReAct: Conversational AI Workspace (Refactored Version)

A modular Streamlit-based platform integrating multiple AI models, real-time search,
web scraping, stock data retrieval, conversation management, and Python code execution capabilities.
"""
import streamlit as st
# Must be the first Streamlit command
st.set_page_config(
    page_title="ReAct Nexus",
    page_icon="🔸",  # Nexus-like symbol (octagonal sign)
    layout="wide"
)

import os
from dotenv import load_dotenv

# Import configuration
from config import WORKSPACE_DIR, load_model_config

# Import SCF module
# (SCFManager is now imported via manager_instance)

# Import tools
from tools import TOOLS

# Import LLM modules
from llm.client import get_openai_client
from llm.executor import run_executor_step

# Import UI components
from ui.sidebar import render_configuration_sidebar, render_conversation_sidebar
from ui.workspace_sidebar import render_workspace_sidebar
from ui.knowledge_base_sidebar import render_knowledge_base_sidebar
from ui.chat import (
    display_messages, display_plan_progress, display_execution_results,
    handle_execution_step, handle_plan_completion, handle_plan_failure,
    process_user_input
)

# Import utilities
from utils.conversation import migrate_conversations_schema

# --- Configuration & Constants ---
load_dotenv()  # Load .env file if it exists

# Initialize Knowledge Manager
from storage.knowledge_manager import KnowledgeManager

# Create knowledge manager instance and set it in the tools module
knowledge_manager = KnowledgeManager(WORKSPACE_DIR)
import tools.knowledge_tools
tools.knowledge_tools.knowledge_manager = knowledge_manager

# Import SCF Manager instance
from scf.manager_instance import scf_manager

# --- Initialize session state variables ---
# Initialize deep_research_mode before using it in the UI
if 'deep_research_mode' not in st.session_state:
    st.session_state.deep_research_mode = False

# --- Streamlit UI ---
# Extremely simplified UI to avoid any potential conflicts
st.title("🔸 ReAct Nexus")

# Function to get current conversation metadata
def get_current_conversation_metadata():
    """Get title and timestamp for the current conversation."""
    if "current_conversation_filename" in st.session_state and st.session_state.current_conversation_filename:
        try:
            # Extract conversation metadata from the file
            import json
            from datetime import datetime
            conv_path = os.path.join(WORKSPACE_DIR, "agent_workspace", st.session_state.current_conversation_filename)
            with open(conv_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                title = data.get('title', 'Untitled')
                created_at = data.get('created_at', '')
                try:
                    dt_obj = datetime.fromisoformat(created_at)
                    timestamp_str = dt_obj.strftime('%Y-%m-%d %H:%M')
                except:
                    timestamp_str = created_at
                return title, timestamp_str
        except Exception as e:
            return None, None
    return None, None


# --- Initialize persistent model configs ---
model_config = load_model_config()

if 'planner_model' not in st.session_state:
    st.session_state.planner_model = model_config.get('planner_model')
if 'executor_model' not in st.session_state:
    st.session_state.executor_model = model_config.get('executor_model')
if 'summarizer_model' not in st.session_state:
    st.session_state.summarizer_model = model_config.get('summarizer_model')
if 'title_model' not in st.session_state:
    st.session_state.title_model = model_config.get('title_model')

# Other session variables
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("LLM_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
if 'base_url' not in st.session_state:
    st.session_state.base_url = os.getenv("LLM_API_BASE_URL", "https://openrouter.ai/api/v1")
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False
# deep_research_mode is now initialized earlier in the file

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "plan" not in st.session_state:
    st.session_state.plan = None
if "current_step_index" not in st.session_state:
    st.session_state.current_step_index = -1
if "context" not in st.session_state:  # Short-term memory for the current task
    st.session_state.context = {}
if "persistent_memory" not in st.session_state:  # Cross-query persistent memory
    st.session_state.persistent_memory = {}
if "message_memories" not in st.session_state:  # Track which messages are included in memory
    st.session_state.message_memories = {}  # Format: {message_index: {"content": "...", "remember": True}}
if "execution_log" not in st.session_state:
    st.session_state.execution_log = []  # To show Reason/Act/Observe
if "current_conversation_filename" not in st.session_state:
    st.session_state.current_conversation_filename = None  # Track current conversation file

# Migrate legacy conversations if needed
migrate_conversations_schema()

# Initialize OpenAI client
client = get_openai_client(st.session_state.api_key, st.session_state.base_url)

# Sidebar navigation
page = st.sidebar.radio("Sidebar Pages", ["Configuration", "Conversation Management", "Workspace", "Knowledge Base"], index=1)

if page == "Configuration":
    render_configuration_sidebar(knowledge_manager)
elif page == "Workspace":
    render_workspace_sidebar()
elif page == "Knowledge Base":
    render_knowledge_base_sidebar(knowledge_manager)
else:  # Conversation Management
    render_conversation_sidebar(client)

# Add styling for expanders
st.markdown("<style>.stExpander {border: none !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1);}</style>", unsafe_allow_html=True)

# Display conversation title and time if a conversation is loaded
title, timestamp = get_current_conversation_metadata()
if title and timestamp:
    st.subheader(f"{title} - {timestamp}")

# Display chat messages
display_messages()

# --- Orchestrator Logic ---
if st.session_state.plan is not None and 0 <= st.session_state.current_step_index < len(st.session_state.plan):
    # Add a reset button for stuck executions
    if st.button("Reset Execution", help="Use this if the execution appears to be stuck"):
        st.session_state.current_step_index = -1
        st.session_state.plan = None
        st.session_state.execution_log = []
        if 'status_container' in st.session_state:
            st.session_state.status_container.empty()
        st.success("Execution reset successfully. You can now submit a new query.")
        st.rerun()
    else:
        # Execute the current step
        handle_execution_step(client)
        # Display plan progress
        display_plan_progress()
# --- Final Response Handling ---
elif st.session_state.plan is not None and st.session_state.current_step_index == len(st.session_state.plan) and len(st.session_state.plan) > 0:
    # Generate final response
    handle_plan_completion(client)
elif st.session_state.current_step_index == -2:  # Halted due to failure
    # Handle plan failure
    handle_plan_failure()

# Display execution results
display_execution_results()

# --- Chat Input ---
if prompt := st.chat_input("Enter your query..."):
    process_user_input(prompt, client)

# Create containers for plan display and log updates
if 'plan_container' not in st.session_state:
    st.session_state.plan_container = st.empty()
if 'log_container' not in st.session_state:
    st.session_state.log_container = st.empty()
# Note: status_container is now created in process_user_input function
