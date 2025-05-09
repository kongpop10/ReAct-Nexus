"""
Sidebar components for the ReAct application.
"""
import os
import json
import streamlit as st
from datetime import datetime
from config import WORKSPACE_DIR, save_model_config
from storage.knowledge_manager import KnowledgeManager
from utils.conversation import load_conversation
from tools import TOOLS

def render_configuration_sidebar(knowledge_manager):
    """Render the configuration sidebar."""
    st.sidebar.subheader("Configuration")

    # LLM Models Configuration in a collapsible section
    with st.sidebar.expander("🤖 LLM Models", expanded=False):
        # API Configuration
        st.session_state.api_key = st.text_input("LLM API Key", type="password", value=st.session_state.api_key)
        st.session_state.base_url = st.text_input("LLM API Base URL", value=st.session_state.base_url)

        # Model Selection
        st.session_state.planner_model = st.text_input("Planner Model", value=st.session_state.planner_model)
        st.session_state.executor_model = st.text_input("Executor Model", value=st.session_state.executor_model)
        st.session_state.summarizer_model = st.text_input("Summarizer Model", value=st.session_state.summarizer_model)
        st.session_state.title_model = st.text_input("Title Generation Model", value=st.session_state.title_model)
    # Persist updated model selections
    save_model_config(st.session_state)

    # SCF Configuration
    with st.sidebar.expander("🧩 Specialized Component Framework", expanded=False):
        st.markdown("### Specialized Component Framework (SCF)")

        # Check if SCF is available
        try:
            from app_config import scf_manager
            if scf_manager:
                # Display available components
                st.markdown("#### Available Components")
                for name, component in scf_manager.components.items():
                    st.markdown(f"**{name}**: {component['description']}")

                # Display routing rules
                st.markdown("#### Routing Rules")
                for rule in scf_manager.routing_rules:
                    st.markdown(f"- Pattern: `{rule['pattern']}` → Component: **{rule['component']}**")
            else:
                st.warning("SCF manager is not initialized")
        except (ImportError, AttributeError):
            st.error("SCF is not available. Make sure the SCF module is properly installed.")

    # Memory Management UI
    with st.sidebar.expander("🧠 Conversation Memory", expanded=False):
        # Display current memory items
        st.subheader("Current Memory Items")

        # Separate message memories from other memories
        message_memories = {k: v for k, v in st.session_state.persistent_memory.items() if k.startswith('message_')}
        other_memories = {k: v for k, v in st.session_state.persistent_memory.items() if not k.startswith('message_') and not k.startswith('kb_')}
        kb_memories = {k: v for k, v in st.session_state.persistent_memory.items() if k.startswith('kb_')}

        # Display message memories first
        if message_memories:
            st.markdown("### 💬 Message Memories")
            for key, value in message_memories.items():
                # Extract message index
                try:
                    msg_idx = int(key.split('_')[1])
                    # Get the original message if available
                    if 0 <= msg_idx < len(st.session_state.messages):
                        original_msg = st.session_state.messages[msg_idx]
                        st.markdown(f"**Message {msg_idx} ({original_msg['role']})**")
                        st.markdown(str(value)[:500] + ('...' if len(str(value)) > 500 else ''))
                    else:
                        st.markdown(f"**{key}**")
                        st.markdown(str(value)[:500] + ('...' if len(str(value)) > 500 else ''))
                except:
                    st.markdown(f"**{key}**")
                    st.markdown(str(value)[:500] + ('...' if len(str(value)) > 500 else ''))

        # Display knowledge base memories
        if kb_memories:
            st.markdown("### 📖 Knowledge Base Memories")
            for key, value in kb_memories.items():
                st.markdown(f"**{key}**")
                st.markdown(str(value)[:500] + ('...' if len(str(value)) > 500 else ''))

        # Display other memories
        if other_memories:
            st.markdown("### 🔑 Custom Memories")
            for key, value in other_memories.items():
                st.markdown(f"**{key}**")
                st.markdown(str(value)[:500] + ('...' if len(str(value)) > 500 else ''))

        # Show message if no memories
        if not message_memories and not other_memories and not kb_memories:
            st.info("No memory items stored yet.")

        # Add a button to clear all memory
        if message_memories or other_memories or kb_memories:
            if st.button("Clear All Memory"):
                st.session_state.persistent_memory = {}
                st.session_state.context = {}
                st.session_state.message_memories = {}
                st.success("Memory cleared successfully!")
                st.rerun()

    # Tools Available in a collapsible section
    with st.sidebar.expander("🛠️ Tools Available", expanded=False):
        st.markdown(f"`{', '.join(TOOLS.keys())}`")
        st.warning("**Security Note:** `execute_python` uses `exec()` and is **not secure**. Use with extreme caution and only trusted code/inputs in a local, controlled environment.")

    # Add debug mode toggle in sidebar
    with st.sidebar.expander("🐞 Debug Options", expanded=False):
        st.session_state.debug_mode = st.toggle("Enable Debug Mode", value=st.session_state.debug_mode)
        if st.session_state.debug_mode:
            st.info("Debug mode is enabled. Verbose output will be shown during execution.")
        else:
            st.info("Debug mode is disabled. Only essential status updates will be shown.")

def render_conversation_sidebar(client):
    """Render the conversation management sidebar."""
    # Modern styling for sidebar and conversation UI
    st.sidebar.markdown(
        """
        <style>
        /* Modern sidebar styling */
        .stButton button {
            padding: 0.4rem 0.6rem;
            font-size: 0.85rem;
            border-radius: 6px;
            transition: all 0.2s ease;
        }
        .stButton button:hover {
            transform: translateY(-1px);
        }
        .stDownloadButton button {
            padding: 0.4rem 0.6rem;
            font-size: 0.85rem;
            border-radius: 6px;
        }
        .stTextInput label, .stSelectbox label {
            font-size: 0.85rem;
            font-weight: 500;
        }
        .stSidebar .block-container {
            padding-top: 0.4rem;
            padding-bottom: 0.4rem;
        }

        /* Make expanders more compact */
        .stSidebar .streamlit-expanderHeader {
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
        }

        /* Make expander content more compact */
        .stSidebar .streamlit-expanderContent {
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
        }

        /* Reduce spacing between sidebar elements */
        .stSidebar [data-testid="stVerticalBlock"] > div {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        /* Make subheaders more compact */
        .stSidebar h3 {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }

        /* Make form elements more compact */
        .stSidebar .stForm > div {
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
        }

        /* Reduce spacing between form elements */
        .stSidebar .stForm [data-testid="stVerticalBlock"] > div {
            margin-bottom: 0.4rem !important;
        }

        /* Make text inputs more compact */
        .stSidebar .stTextInput > div {
            margin-bottom: 0.4rem !important;
        }

        /* Make radio buttons more compact */
        .stSidebar .stRadio > div {
            margin-bottom: 0.4rem !important;
        }

        /* Reduce spacing in radio button options */
        .stSidebar .stRadio [data-testid="stVerticalBlock"] > div {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }

        /* Conversation cards styling */
        .conversation-card {
            border-radius: 8px;
            padding: 8px 8px;
            margin-bottom: 0px; /* Reduced from 2px */
            border-left: 3px solid #4e8cff;
        }
        .conversation-title {
            font-weight: 500;
            margin-bottom: 0px; /* Reduced from 4px */
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .conversation-actions {
            display: flex;
            gap: 4px;
            margin-top: 0px; /* Reduced from 1px */
        }
        /* Compact button styling */
        .stButton button {
            min-height: 0;
            line-height: 1;
            padding: 0.6rem 0.6rem;
        }
        /* Conversation container spacing */
        .stSidebar [data-testid="stVerticalBlock"] > div:has(> div > [data-testid="stHorizontalBlock"]) {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        /* Reduce spacing between conversation titles */
        .stSidebar [data-testid="stVerticalBlock"] > div {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        /* Reduce spacing for horizontal rule */
        .stSidebar hr {
            margin: 1px 0 !important;
            padding: 0 !important;
        }
        /* Align delete button with New Chat button edge */
        .stSidebar [data-testid="stHorizontalBlock"] {
            padding-right: 0 !important;
            margin-right: 0 !important;
            width: 100% !important;
        }
        /* Make delete button more compact and aligned to the right */
        .stSidebar [data-testid="stHorizontalBlock"] > div:nth-child(2) {
            padding-left: 0 !important;
            padding-right: 0 !important;
        }
        /* Make delete button fill its column */
        .stSidebar [data-testid="stHorizontalBlock"] > div:nth-child(2) button {
            width: 100% !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            display: flex;
            justify-content: center;
        }

        /* Chat message styling */
        .chat-message {
            padding: 10px 15px;
            border-radius: 12px;
            margin-bottom: 10px;
            max-width: 85%;
        }
        .user-message {
            /* Removed margin-left: auto to align with default Streamlit alignment */
            border-bottom-right-radius: 4px;
        }
        .assistant-message {
            margin-right: auto;
            border-bottom-left-radius: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Load conversation index metadata
    conv_index_path = os.path.join(WORKSPACE_DIR, "agent_workspace", "conversations_index.json")
    conversations = []
    try:
        with open(conv_index_path, "r", encoding="utf-8") as f:
            conversations = json.load(f)
            if not isinstance(conversations, list):
                conversations = []
    except Exception:
        conversations = []

    # Deep Research Mode toggle switch
    st.sidebar.toggle("🔍 Deep Research Mode",
                     value=st.session_state.deep_research_mode,
                     help="When enabled, the AI will perform more thorough research with more detailed results",
                     key="deep_research_toggle")

    # Update session state if toggle value changes
    if 'deep_research_toggle' in st.session_state and st.session_state.deep_research_toggle != st.session_state.deep_research_mode:
        st.session_state.deep_research_mode = st.session_state.deep_research_toggle
        st.rerun()

    # Conversations section directly in sidebar (not in expander)
    st.sidebar.subheader("📂 Conversations")
    st.sidebar.button("➕ New Chat", key="new_chat_button",
             on_click=lambda: st.session_state.update({
                 'messages': [],
                 'current_conversation_filename': None,
                 'persistent_memory': {},
                 'message_memories': {},
                 'plan': None,
                 'current_step_index': -1,
                 'execution_log': []
             }),
             use_container_width=True)

    if not conversations:
        st.sidebar.info("No saved conversations found.")
    else:
        for conv in sorted(conversations, key=lambda x: x.get('created_at', ''), reverse=True):
            filename = conv.get('filename')
            title = conv.get('title', 'Untitled')
            created_at = conv.get('created_at', '')
            try:
                dt_obj = datetime.fromisoformat(created_at)
                timestamp_str = dt_obj.strftime('%Y-%m-%d %H:%M')
            except:
                timestamp_str = created_at

            # Create a card-like container for each conversation
            with st.sidebar.container():
                # We still calculate timestamp_str for use in the main UI, but don't display it here
                # Action buttons in a more compact layout with no load button
                # Use the same column ratio as the container width to align with New Chat button
                cols = st.sidebar.columns([4, 1])

                # Make title clickable to load conversation
                if cols[0].button(f"{title}", key=f"load_title_{filename}", help="Click to load conversation", use_container_width=True):
                    st.session_state.messages = load_conversation(filename)
                    # Set the current conversation filename
                    st.session_state.current_conversation_filename = filename
                    st.sidebar.success(f"Loaded: {title}")
                    st.rerun()

                # Compact delete button
                if cols[1].button("🗑️", key=f"delete_{filename}", help="Delete conversation", use_container_width=True):
                    conv_path = os.path.join(WORKSPACE_DIR, "agent_workspace", filename)
                    try:
                        if os.path.exists(conv_path):
                            os.remove(conv_path)

                        # Remove from index and save
                        conversations = [c for c in conversations if c.get('filename') != filename]
                        with open(conv_index_path, "w", encoding="utf-8") as f:
                            json.dump(conversations, f, indent=2)

                        st.sidebar.success("Conversation deleted.")
                        st.rerun()
                    except Exception as e:
                        st.sidebar.warning(f"Failed to delete conversation: {e}")

                # Removed horizontal line between conversations to make UI more compact
