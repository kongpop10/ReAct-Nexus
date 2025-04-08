"""
Conversation management utilities for the ReAct application.
"""
import os
import json
import re
from datetime import datetime
import streamlit as st
from config import WORKSPACE_DIR

def generate_title(messages, client=None):
    """Generate a title based on the conversation messages using the configured LLM model."""
    try:
        # Extract the user's query from messages
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]

        # If we have user messages and a client, use the configured model to generate a title
        if user_messages and client:
            # Combine up to the last 3 user messages for context
            context = "\n".join(user_messages[-3:])

            # Use the configured model to generate a title
            try:
                # Get the title model from session state, with fallback to default
                title_model = st.session_state.get('title_model')

                completion = client.chat.completions.create(
                    model=title_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates concise, descriptive titles for conversations. Create a short title (5-7 words max) that captures the essence of the conversation."},
                        {"role": "user", "content": f"Generate a short, descriptive title for this conversation:\n{context}"}
                    ],
                    temperature=0.3,
                    max_tokens=20
                )

                if completion and completion.choices and completion.choices[0].message.content:
                    title = completion.choices[0].message.content.strip()
                    # Remove quotes if the model added them
                    title = title.strip('"\'')
                    return title
            except Exception as e:
                st.write(f"Error using Gemini for title generation: {str(e)}")
                # Fall back to simple title generation

        # Simple title generation fallback
        if user_messages:
            # Get the most recent user message
            latest_user_message = user_messages[-1]

            # Create a simple title from the first 30 characters of the message
            if len(latest_user_message) > 30:
                title = latest_user_message[:30] + "..."
            else:
                title = latest_user_message

            return title
        else:
            # Fallback to timestamp if no user messages
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            return f"Chat on {timestamp_str}"
    except Exception as e:
        st.write(f"Error generating title: {str(e)}")
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        return f"Chat on {timestamp_str}"

def migrate_conversations_schema():
    """Scan and migrate legacy conversation JSON files to extended schema, and build index."""
    import os
    import json
    import re
    from datetime import datetime

    conv_dir = os.path.join(WORKSPACE_DIR, 'agent_workspace')
    index = []

    pattern = re.compile(r'^conversation_(\d{8}_\d{6})\.json$')

    try:
        files = os.listdir(conv_dir)
    except Exception:
        files = []

    for fname in files:
        match = pattern.match(fname)
        if not match:
            continue

        timestamp_str = match.group(1)  # e.g., 20250404_092615
        dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        created_at = dt.isoformat()
        title = f"Chat on {dt.strftime('%Y-%m-%d %H:%M')}"

        fpath = os.path.join(conv_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            data = json.loads(content)
        except Exception:
            continue  # skip broken files

        # If already migrated (dict with 'messages' key), skip updating file
        if isinstance(data, dict) and 'messages' in data:
            schema = data
        elif isinstance(data, list):
            schema = {
                'title': title,
                'created_at': created_at,
                'messages': data
            }
            # Save back migrated schema
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2)
            except Exception:
                continue
        else:
            continue  # skip unknown formats

        index.append({
            'filename': fname,
            'title': schema.get('title', title),
            'created_at': schema.get('created_at', created_at)
        })

    # Save conversations_index.json
    index_path = os.path.join(conv_dir, 'conversations_index.json')
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
    except Exception:
        pass

def load_conversation(filename):
    """Load a conversation from a JSON file."""
    path = os.path.join(WORKSPACE_DIR, 'agent_workspace', filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return []

    if isinstance(data, dict) and 'messages' in data:
        return data['messages']
    elif isinstance(data, list):
        return data
    else:
        return []

def save_conversation(filename, messages, title=None, created_at=None):
    """Save a conversation to a JSON file."""
    from datetime import datetime
    import os

    conv_dir = os.path.join(WORKSPACE_DIR, 'agent_workspace')
    # Ensure the directory exists
    if not os.path.exists(conv_dir):
        os.makedirs(conv_dir)
    path = os.path.join(conv_dir, filename)

    if created_at is None:
        # Infer from filename timestamp
        try:
            ts_part = filename.split('_')[1] + '_' + filename.split('_')[2].split('.')[0]
            dt = datetime.strptime(ts_part, '%Y%m%d_%H%M%S')
            created_at = dt.isoformat()
        except Exception:
            created_at = datetime.now().isoformat()

    if title is None:
        try:
            dt = datetime.fromisoformat(created_at)
            title = f"Chat on {dt.strftime('%Y-%m-%d %H:%M')}"
        except Exception:
            title = "Chat"

    schema = {
        'title': title,
        'created_at': created_at,
        'messages': messages
    }

    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
    except Exception:
        return

    # Update conversations_index.json
    index_path = os.path.join(conv_dir, 'conversations_index.json')
    try:
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = []
    except Exception:
        index = []

    # Remove existing record with same filename
    index = [item for item in index if item.get('filename') != filename]
    index.append({
        'filename': filename,
        'title': title,
        'created_at': created_at
    })

    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
    except Exception:
        pass

def auto_save_conversation(messages, client, current_filename=None):
    """Automatically save conversation, either updating existing file or creating a new one."""
    if not messages or len(messages) == 0:
        return None, None

    # Determine if we should create a new file or update existing one
    if current_filename is None:
        # Create a new file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"
        created_at = datetime.now().isoformat()

        # Generate title using the configured model
        generated_title = generate_title(messages, client)

        # Save conversation with metadata
        save_conversation(filename, messages, title=generated_title, created_at=created_at)

        # Show a toast notification
        st.toast(f"Saved new conversation: {generated_title}", icon="✅")

        return filename, generated_title
    else:
        # Update existing file
        conv_dir = os.path.join(WORKSPACE_DIR, 'agent_workspace')
        path = os.path.join(conv_dir, current_filename)

        # Read existing data to preserve title and created_at
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                title = data.get('title', None)
                created_at = data.get('created_at', None)
        except Exception:
            # If file doesn't exist or is corrupted, create new metadata
            title = None
            created_at = None

        # Save updated conversation
        save_conversation(current_filename, messages, title=title, created_at=created_at)

        # Show a toast notification
        st.toast(f"Updated conversation", icon="✅")

        return current_filename, title
