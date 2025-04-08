# Knowledge Base Implementation Plan for ReAct

## Overview
This document outlines the plan for implementing a persistent knowledge base feature in the ReAct conversational AI workspace. The knowledge base will support both web-scraped content and local markdown files, persisting across conversations.

## 1. Storage Structure

### Directory Layout
```
WORKSPACE_DIR/
├── knowledge_base/
│   ├── web_sources/      # Scraped website content
│   ├── local_sources/    # Included MD files
│   └── knowledge_index.json
```

### Knowledge Entry Schema
```json
{
  "id": "unique_id",
  "type": "web|local",
  "source": "url_or_filepath",
  "title": "auto_generated_or_filename",
  "added_date": "timestamp",
  "last_updated": "timestamp",
  "memory_key": "kb_unique_key",
  "status": "active|archived"
}
```

## 2. Core Components

### A. Knowledge Manager Module (`storage/knowledge_manager.py`)
- Knowledge entry CRUD operations
- Index management
- Content storage/retrieval
- Memory key generation
- Deduplication handling

### B. Knowledge Base UI (`app.py` sidebar)
- "Knowledge Base" section in sidebar
- List of current knowledge sources
- Add/Remove knowledge controls
- Knowledge source status indicators

## 3. Integration Points

### A. URL Scraping Enhancement
- Enhance `detect_url_scrape_request()`
- Add "save to knowledge base" option
- Dual storage: session memory + knowledge base

### B. Local MD Files Support
- File picker in sidebar
- MD content validation and processing
- Memory key generation for files

## 4. Memory System Enhancement
- Modify `memory_get`/`memory_set`
- Add knowledge base prefix to memory keys
- Priority order: session memory > knowledge base

## 5. Command Detection
New command phrases:
- "add to knowledge base"
- "include file as knowledge"
- "list knowledge sources"
- "remove from knowledge base"

## 6. Search and Retrieval
- Knowledge base search functionality
- Context injection into conversations
- Source attribution for responses

## Implementation Notes
- Maintain backward compatibility with current memory system
- Leverage existing `web_scrape()` functionality
- Ensure thread-safe operations for knowledge base access
- Implement proper error handling and validation

## Future Considerations
- Knowledge base versioning
- Content update mechanisms
- Knowledge source categorization
- Search optimization
- Export/Import functionality