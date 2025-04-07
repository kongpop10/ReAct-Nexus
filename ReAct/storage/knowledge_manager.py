import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, BinaryIO
import shutil
import tempfile

class KnowledgeManager:
    """
    Manages the knowledge base for the ReAct agent.
    Handles storage, retrieval, and indexing of knowledge sources.
    """

    def __init__(self, workspace_dir: str):
        """
        Initialize the knowledge manager with the workspace directory.

        Args:
            workspace_dir: The base workspace directory path
        """
        self.workspace_dir = workspace_dir
        self.kb_dir = os.path.join(workspace_dir, "knowledge_base")
        self.web_sources_dir = os.path.join(self.kb_dir, "web_sources")
        self.local_sources_dir = os.path.join(self.kb_dir, "local_sources")
        self.index_file = os.path.join(self.kb_dir, "knowledge_index.json")

        # Create directory structure if it doesn't exist
        self._ensure_directories()

        # Load the knowledge index
        self.index = self._load_index()

    def _ensure_directories(self) -> None:
        """Create the necessary directory structure if it doesn't exist."""
        os.makedirs(self.kb_dir, exist_ok=True)
        os.makedirs(self.web_sources_dir, exist_ok=True)
        os.makedirs(self.local_sources_dir, exist_ok=True)

    def _load_index(self) -> List[Dict[str, Any]]:
        """Load the knowledge index from the index file."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_index(self) -> None:
        """Save the knowledge index to the index file."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2)
        except IOError as e:
            print(f"Error saving knowledge index: {e}")

    def _generate_memory_key(self, entry_type: str, source: str) -> str:
        """
        Generate a unique memory key for a knowledge entry.

        Args:
            entry_type: Type of entry ('web' or 'local')
            source: Source URL or filepath

        Returns:
            A unique memory key for the entry
        """
        if entry_type == 'web':
            # Extract domain from URL
            from urllib.parse import urlparse
            domain = urlparse(source).netloc
            # Remove www. and .com/.org/etc. to create a clean key
            domain = domain.replace('www.', '')
            domain = domain.split('.')[0]  # Get the main domain name
            return f"kb_web_{domain}_{int(time.time())}"
        else:  # local
            # Use filename without extension
            filename = os.path.basename(source)
            name = os.path.splitext(filename)[0]
            return f"kb_local_{name}_{int(time.time())}"

    def _generate_id(self) -> str:
        """Generate a unique ID for a knowledge entry."""
        return str(uuid.uuid4())

    def add_web_source(self, url: str, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a web source to the knowledge base.

        Args:
            url: The URL of the web source
            content: The content of the web source
            title: Optional title for the source (auto-generated if None)

        Returns:
            The created knowledge entry
        """
        # Generate a unique ID and memory key
        entry_id = self._generate_id()
        memory_key = self._generate_memory_key('web', url)

        # Generate a title if not provided
        if not title:
            # Use domain name as title
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            title = f"Web content from {domain}"

        # Create the entry
        timestamp = datetime.now().isoformat()
        entry = {
            "id": entry_id,
            "type": "web",
            "source": url,
            "title": title,
            "added_date": timestamp,
            "last_updated": timestamp,
            "memory_key": memory_key,
            "status": "active"
        }

        # Save the content to a file
        content_file = os.path.join(self.web_sources_dir, f"{entry_id}.txt")
        try:
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except IOError as e:
            return {"error": f"Failed to save content: {e}"}

        # Add to index and save
        self.index.append(entry)
        self._save_index()

        return entry

    def add_local_source(self, filepath: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a local markdown file to the knowledge base.

        Args:
            filepath: Path to the local markdown file
            title: Optional title for the source (filename if None)

        Returns:
            The created knowledge entry or error dict
        """
        # Check if file exists and is markdown
        if not os.path.exists(filepath):
            return {"error": f"File not found: {filepath}"}

        if not filepath.lower().endswith('.md'):
            return {"error": "Only markdown (.md) files are supported"}

        # Generate a unique ID and memory key
        entry_id = self._generate_id()
        memory_key = self._generate_memory_key('local', filepath)

        # Use filename as title if not provided
        if not title:
            title = os.path.basename(filepath)

        # Create the entry
        timestamp = datetime.now().isoformat()
        entry = {
            "id": entry_id,
            "type": "local",
            "source": filepath,
            "title": title,
            "added_date": timestamp,
            "last_updated": timestamp,
            "memory_key": memory_key,
            "status": "active"
        }

        # Copy the file to the local sources directory
        dest_path = os.path.join(self.local_sources_dir, f"{entry_id}.md")
        try:
            shutil.copy2(filepath, dest_path)
        except IOError as e:
            return {"error": f"Failed to copy file: {e}"}

        # Add to index and save
        self.index.append(entry)
        self._save_index()

        return entry

    def get_entry_content(self, entry_id: str) -> str:
        """
        Get the content of a knowledge entry.

        Args:
            entry_id: The ID of the entry

        Returns:
            The content of the entry or error message
        """
        # Find the entry in the index
        entry = next((e for e in self.index if e["id"] == entry_id), None)
        if not entry:
            return f"Entry not found: {entry_id}"

        # Determine the file path based on entry type
        if entry["type"] == "web":
            file_path = os.path.join(self.web_sources_dir, f"{entry_id}.txt")
        else:  # local
            file_path = os.path.join(self.local_sources_dir, f"{entry_id}.md")

        # Read the content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError as e:
            return f"Error reading content: {e}"

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """Get all knowledge entries."""
        return self.index

    def get_active_entries(self) -> List[Dict[str, Any]]:
        """Get all active knowledge entries."""
        return [entry for entry in self.index if entry["status"] == "active"]

    def get_entry_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a knowledge entry by ID."""
        return next((e for e in self.index if e["id"] == entry_id), None)

    def get_entry_by_memory_key(self, memory_key: str) -> Optional[Dict[str, Any]]:
        """Get a knowledge entry by memory key."""
        return next((e for e in self.index if e["memory_key"] == memory_key), None)

    def update_entry_status(self, entry_id: str, status: str) -> Dict[str, Any]:
        """
        Update the status of a knowledge entry.

        Args:
            entry_id: The ID of the entry
            status: The new status ('active' or 'archived')

        Returns:
            The updated entry or error dict
        """
        if status not in ['active', 'archived']:
            return {"error": "Invalid status. Must be 'active' or 'archived'"}

        entry = self.get_entry_by_id(entry_id)
        if not entry:
            return {"error": f"Entry not found: {entry_id}"}

        entry["status"] = status
        entry["last_updated"] = datetime.now().isoformat()
        self._save_index()

        return entry

    def delete_entry(self, entry_id: str) -> Dict[str, str]:
        """
        Delete a knowledge entry.

        Args:
            entry_id: The ID of the entry

        Returns:
            Status message
        """
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            return {"error": f"Entry not found: {entry_id}"}

        # Remove the file
        if entry["type"] == "web":
            file_path = os.path.join(self.web_sources_dir, f"{entry_id}.txt")
        else:  # local
            file_path = os.path.join(self.local_sources_dir, f"{entry_id}.md")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except IOError as e:
            return {"error": f"Failed to delete file: {e}"}

        # Remove from index
        self.index = [e for e in self.index if e["id"] != entry_id]
        self._save_index()

        return {"status": "success", "message": f"Entry {entry_id} deleted"}

    def search_entries(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for knowledge entries matching the query.

        Args:
            query: The search query

        Returns:
            List of matching entries
        """
        query = query.lower()
        results = []

        for entry in self.index:
            # Search in title
            if query in entry["title"].lower():
                results.append(entry)
                continue

            # Search in content
            content = self.get_entry_content(entry["id"])
            if query in content.lower():
                results.append(entry)

        return results

    def get_all_content_for_memory(self) -> Dict[str, str]:
        """
        Get all active knowledge content for memory integration.

        Returns:
            Dictionary mapping memory keys to content
        """
        memory_dict = {}

        for entry in self.get_active_entries():
            content = self.get_entry_content(entry["id"])
            memory_dict[entry["memory_key"]] = content

        return memory_dict

    def add_uploaded_file(self, uploaded_file: BinaryIO, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Add an uploaded file to the knowledge base.

        Args:
            uploaded_file: The uploaded file object from Streamlit's file_uploader
            title: Optional title for the source (filename if None)

        Returns:
            The created knowledge entry or error dict
        """
        # Check if file is markdown
        filename = uploaded_file.name
        if not filename.lower().endswith('.md'):
            return {"error": "Only markdown (.md) files are supported"}

        # Create a temporary file to store the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as temp_file:
            temp_filepath = temp_file.name
            # Write the uploaded file content to the temp file
            temp_file.write(uploaded_file.getvalue())

        try:
            # Generate a unique ID and memory key
            entry_id = self._generate_id()
            memory_key = self._generate_memory_key('local', filename)

            # Use filename as title if not provided
            if not title:
                title = filename

            # Create the entry
            timestamp = datetime.now().isoformat()
            entry = {
                "id": entry_id,
                "type": "local",
                "source": f"Uploaded: {filename}",  # Mark as uploaded file
                "title": title,
                "added_date": timestamp,
                "last_updated": timestamp,
                "memory_key": memory_key,
                "status": "active"
            }

            # Copy the file to the local sources directory
            dest_path = os.path.join(self.local_sources_dir, f"{entry_id}.md")
            try:
                shutil.copy2(temp_filepath, dest_path)
            except IOError as e:
                return {"error": f"Failed to copy file: {e}"}

            # Add to index and save
            self.index.append(entry)
            self._save_index()

            return entry
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
