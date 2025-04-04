"""Handles saving, loading, auto-saving, and migrating conversations."""

import os
import json
from datetime import datetime
import streamlit as st

def migrate_conversations_schema():
    """Scan and migrate legacy conversation JSON files to extended schema, and build index."""
    conv_dir = os.path.join(WORKSPACE_DIR, 'agent_workspace')
    index = []

    import re
    pattern = re.compile(r'^conversation_(\d{8}_\d{6})\.json$')

    try:
        files = os.listdir(conv_dir)
    except Exception:
        files = []

    for fname in files:
        match = pattern.match(fname)
        if not match:
            continue

        timestamp_str = match.group(1)
        dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        created_at = dt.isoformat()
        title = f"Chat on {dt.strftime('%Y-%m-%d %H:%M')}"

        fpath = os.path.join(conv_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            data = json.loads(content)
        except Exception:
            continue

        if isinstance(data, dict) and 'messages' in data:
            schema = data
        elif isinstance(data, list):
            schema = {
                'title': title,
                'created_at': created_at,
                'messages': data
            }
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2)
            except Exception:
                continue
        else:
            continue

        index.append({
            'filename': fname,
            'title': schema.get('title', title),
            'created_at': schema.get('created_at', created_at)
        })

    index_path = os.path.join(conv_dir, 'conversations_index.json')
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
    except Exception:
        pass

def load_conversation(filename):
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
    conv_dir = os.path.join(WORKSPACE_DIR, 'agent_workspace')
    if not os.path.exists(conv_dir):
        os.makedirs(conv_dir)
    path = os.path.join(conv_dir, filename)

    if created_at is None:
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

    index_path = os.path.join(conv_dir, 'conversations_index.json')
    try:
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = []
    except Exception:
        index = []

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

    if current_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"
        created_at = datetime.now().isoformat()

        generated_title = generate_title(messages, client)

        save_conversation(filename, messages, title=generated_title, created_at=created_at)

        st.toast(f"Saved new conversation: {generated_title}", icon="✅")

        return filename, generated_title
    else:
        conv_dir = os.path.join(WORKSPACE_DIR, 'agent_workspace')
        path = os.path.join(conv_dir, current_filename)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                title = data.get('title', None)
                created_at = data.get('created_at', None)
        except Exception:
            title = None
            created_at = None

        save_conversation(current_filename, messages, title=title, created_at=created_at)

        st.toast(f"Updated conversation", icon="✅")

        return current_filename, title