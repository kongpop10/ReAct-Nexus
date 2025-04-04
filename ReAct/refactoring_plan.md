# Refactoring Plan for `app.py`

## Goals
- **Separate concerns** into logically distinct modules
- **Isolate functionalities** to enable easier testing and maintenance
- **Simplify the main app entry point** to focus mainly on orchestration and UI

---

## High-Level Modularization Strategy

```mermaid
flowchart TD
    A[Main app.py (Streamlit UI + Orchestration)]
    subgraph Modules
        B[ai_client.py\n(OpenAI interaction)]
        C[file_utils.py\n(Read/Write/List/Delete)]
        D[conversation_manager.py\n(Save/Load/Auto-save/Migrate)]
        E[memory_manager.py\n(Memory operations)]
        F[web_tools.py\n(Search & Scrape)]
        G[stock_data.py\n(Stock info retrieval)]
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
```

---

## Step-by-Step Plan

### 1. **Create Dedicated Modules**

- **ai_client.py**
  - `generate_title`
  - `run_planner`
  - `run_executor_step`
  - `get_openai_client`
  - `generate_final_response`

- **file_utils.py**
  - `read_file`
  - `write_file`
  - `list_files`
  - `delete_file`

- **conversation_manager.py**
  - `load_conversation`
  - `save_conversation`
  - `auto_save_conversation`
  - `migrate_conversations_schema`

- **memory_manager.py**
  - `memory_get`
  - `memory_set`
  - `memory_list`
  - `update_message_memory`
  - `update_memory_from_messages`

- **web_tools.py**
  - `web_search`
  - `web_scrape`

- **stock_data.py**
  - `get_stock_data`

---

### 2. **Refactor Functions**

- Move the above functions into their respective modules as-is initially to avoid breaking changes.
- Add appropriate imports and export statements.

---

### 3. **Simplify `app.py`**

- Keep only:
  - The **Streamlit UI code** (currently around lines 1237–1379)
  - High-level orchestration logic
- Replace direct function bodies with **imports** from the new modules.
- This reduces `app.py` to mostly UI and high-level flow.

---

### 4. **Refine Interfaces**

- Once modularized, gradually:
  - Clarify function signatures
  - Add type annotations if missing
  - Improve docstrings
  - Handle errors gracefully within modules (raise exceptions, avoid crashing app)

---

### 5. **Testing**

- Write or enhance **unit tests** for each module
- Mock external API calls (OpenAI, web scraping) during tests
- Test file operations with temporary directories/files

---

### 6. **Documentation**

- Add module-level docstrings explaining purpose and usage
- Update project README to reflect new structure

---

### 7. **Optional Enhancements**

- Introduce **dependency injection** to manage clients (OpenAI, web scraping)
- Use **asyncio** if any functions are I/O bound (e.g., API calls, file I/O)
- Add **logging** instead of print statements for better traceability

---

## Summary

This modular approach separates file handling, AI interaction, conversation management, memory, web tools, and stock data functionalities, improving readability, maintainability, and testability. The main `app.py` will be simplified to coordinate these modules and handle the UI logic.