"""Manages memory storage, retrieval, and updates."""

import streamlit as st

def memory_get(key: str) -> str:
    """Retrieves a value from memory by key."""
    st.write(f"TOOL: memory_get(key='{key}')")
    value = st.session_state.context.get(key, None)
    if value is None:
        return f"No value found for key '{key}' in memory."
    return str(value)

def memory_set(key: str, value: str) -> str:
    """Stores a value in memory with the given key."""
    st.write(f"TOOL: memory_set(key='{key}', value='{value}')")
    st.session_state.context[key] = value
    return f"Successfully stored value for key '{key}' in memory."

def memory_list() -> str:
    """Lists all keys currently stored in memory."""
    st.write(f"TOOL: memory_list()")
    memory_keys = [key for key in st.session_state.context.keys() if not key.startswith('step_')]
    if not memory_keys:
        return "No named memory items found."
    return "Memory keys: " + ", ".join(memory_keys)

def update_message_memory(message_index, remember=True):
    """Update whether a message should be remembered or not."""
    if 0 <= message_index < len(st.session_state.messages):
        message = st.session_state.messages[message_index]
        st.session_state.message_memories[message_index] = {
            "content": message["content"],
            "role": message["role"],
            "remember": remember
        }
        update_memory_from_messages()
        return True
    return False

def update_memory_from_messages():
    """Extract information from messages and update the persistent memory."""
    message_memory_keys = [k for k in st.session_state.persistent_memory.keys()
                          if k.startswith('message_')]
    for key in message_memory_keys:
        if key in st.session_state.persistent_memory:
            del st.session_state.persistent_memory[key]

    for idx, memory_data in st.session_state.message_memories.items():
        if memory_data["remember"] and memory_data["role"] == "assistant":
            memory_key = f"message_{idx}"
            st.session_state.persistent_memory[memory_key] = memory_data["content"]

    st.session_state.context = st.session_state.persistent_memory.copy()
