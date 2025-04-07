# Plan-ReAct Agent: Advanced Conversational AI Workspace

A **modular Streamlit-based platform** integrating multiple AI models, real-time search, web scraping, stock data retrieval, conversation management, and Python code execution capabilities with advanced planning and execution features.

---

## Features

- **Conversational AI**: Chat with various LLMs through compatible API endpoints
- **Automated Title Generation** for conversations using LLMs
- **Web Search**: Real-time queries via Tavily API
- **Web Scraping**: Extract content from URLs with BeautifulSoup and advanced scraping via Firecrawl
- **Stock Data Retrieval**: Fetch real-time stock info via Alpha Vantage API
- **Python Code Execution**: Run code snippets dynamically (demo purposes only; unsafe for production)
- **Conversation Management**:
  - Save/load conversations with metadata (title, timestamp)
  - Automatic conversation saving and indexing
  - Schema migration for legacy files
- **File Operations**: Read, write, delete, list files within a workspace directory
- **Memory Management**: Store and manage conversation context and variables
- **Specialized Component Framework (SCF)**:
  - Break down complex problems into specialized sub-problems
  - Route queries to specialized components (Researcher, Analyst, Planner, Executor, Synthesizer)
  - Component-specific system prompts and tool filtering
- **Dynamic Plan Adjustment**:
  - Recover from failures with RETRY, REPLACE, SKIP, or ABORT actions
  - Add additional steps during execution based on new information
  - Automatic dependency management when modifying plans
- **Cross-Query Memory**:
  - Maintain context across multiple queries within the same conversation
  - Toggle inclusion/exclusion of previous responses in memory

---

## Installation

1. **Clone the repository**

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

### Dependencies

- streamlit
- openai
- requests
- python-dotenv
- tavily-python
- firecrawl-py

---

## Configuration

Create a `.env` file in the root directory and add your API keys:

```
# You can use either LLM_API_KEY or OPENROUTER_API_KEY (LLM_API_KEY takes precedence)
LLM_API_KEY=your_llm_api_key
# Optional: LLM_API_BASE_URL=your_llm_api_base_url

TAVILY_API_KEY=your_tavily_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FIRECRAWL_API_KEY=your_firecrawl_key
```

These are required for AI completions, web search, stock data, and advanced web scraping/crawling respectively.

### Model Configuration

The application uses different models for different tasks:

- **Planner Model**: Used for generating execution plans (default: `google/gemini-2.0-flash-thinking-exp:free`)
- **Executor Model**: Used for executing plan steps (default: `google/gemini-2.0-flash-exp:free`)
- **Summarizer Model**: Used for generating final responses (default: `google/gemini-2.0-flash-thinking-exp:free`)
- **Title Model**: Used for generating conversation titles (default: `google/gemini-2.0-flash-exp:free`)

Note: The Summarizer Model is different from the Synthesizer component in the Specialized Component Framework. The Summarizer Model is used for generating the final response to the user, while the Synthesizer component is a specialized agent that uses the Planner and Executor models with a specific system prompt focused on combining information from multiple sources.

These can be configured in the UI or by editing the `model_config.json` file.

### SCF Configuration

Specialized Component Framework can be configured by editing the `scf_config.json` file. This file defines the specialized components and their routing rules.

The SCF includes several specialized components:

- **Researcher**: Specialized in gathering information from multiple sources
- **Analyst**: Specialized in analyzing and evaluating information
- **Planner**: Specialized in organizing and structuring tasks
- **Executor**: Specialized in implementing and running operations
- **Synthesizer**: Specialized in combining information from multiple sources into coherent outputs

Each component uses the same LLM models configured in `model_config.json` but with different system prompts and tool capabilities optimized for their specific functions.

---

## Usage

Run the app with Streamlit using either the original or refactored version:

```bash
# Original version
streamlit run app.py

# Refactored version (recommended)
streamlit run main.py
# Or use the provided scripts
./run.sh  # Linux/Mac
run.bat   # Windows
```

Navigate to the local URL provided by Streamlit to access the interface.

---

## Project Structure

The application has been refactored for improved modularity and maintainability:

```
/ReAct
│
├── config.py                # Configuration settings and constants
│
├── main.py                  # New entry point (refactored version)
├── app.py                   # Original entry point (kept for reference)
│
├── tools/                   # Tool implementations
│   ├── __init__.py          # Tool registry
│   ├── web_tools.py         # Web search and scraping tools
│   ├── file_tools.py        # File operations
│   ├── memory_tools.py      # Memory management
│   ├── knowledge_tools.py   # Knowledge base operations
│   ├── execution_tools.py   # Python execution
│   ├── stock_tools.py       # Stock data retrieval
│
├── llm/                     # LLM interaction
│   ├── __init__.py
│   ├── client.py            # Client initialization
│   ├── planner.py           # Planning functions
│   ├── executor.py          # Execution functions
│   ├── summarizer.py        # Response generation
│   ├── plan_adjuster.py     # Dynamic plan adjustment
│
├── scf/                     # Specialized Component Framework
│   ├── __init__.py
│   ├── scf_manager.py       # SCF coordination
│   ├── manager_instance.py  # SCF instance initialization
├── scf_config.json          # Component definitions
│
├── ui/                      # UI components
│   ├── __init__.py
│   ├── chat.py              # Chat interface
│   ├── sidebar.py           # Sidebar components
│
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── conversation.py      # Conversation management
│   ├── formatting.py        # Text formatting
│   ├── status.py            # Status indicators
│
├── storage/                 # Storage management
│   ├── __init__.py
│   ├── knowledge_manager.py # Knowledge base management
│   ├── file_utils.py        # File operations
│
├── data_acquisition/        # External data collection
│   ├── __init__.py
│   ├── news_scraper.py      # Web scraping
│   ├── process_search_results.py # Search result processing
│
├── processing/              # Data processing
│   ├── __init__.py
│   ├── format_results.py    # Result formatting
│
├── agent_workspace/         # Workspace directory for file operations
│
├── run_refactored.sh        # Script to run refactored version (Linux/Mac)
├── run_refactored.bat       # Script to run refactored version (Windows)
├── requirements.txt
├── README.md
├── REFACTORING.md           # Refactoring documentation
├── COMPLEX_QUERY_IMPROVEMENTS.md # MCP documentation
├── .gitignore
```

### Summary of key folders and files:

- **`config.py`**: Centralized configuration settings
- **`main.py`**: New entry point for the refactored application
- **`tools/`**: All tool implementations with a central registry
- **`llm/`**: LLM interaction, planning, execution, and response generation
- **`scf/`**: Specialized Component Framework for complex queries
- **`ui/`**: User interface components
- **`utils/`**: Utility functions
- **`storage/`**: Persistent storage and knowledge management
- **`data_acquisition/`**: External data collection
- **`processing/`**: Data post-processing
- **`agent_workspace/`**: Workspace directory for file operations

---

## Additional Notes

- The application has been refactored for improved modularity, clarity, and scalability.
- The Specialized Component Framework (SCF) system allows handling complex queries more effectively.
- Dynamic Plan Adjustment enables recovery from failures and adaptation to new information.
- Cross-Query Memory maintains context across multiple queries within the same conversation.
- The app **allows arbitrary Python code execution**, which is **unsafe for production**—use only in a secure, sandboxed environment.
- For detailed information about the refactoring, see `REFACTORING.md`.
- For detailed information about complex query improvements, see `COMPLEX_QUERY_IMPROVEMENTS.md`.

---

## License

MIT License

---

## Credits

- Built with [Streamlit](https://streamlit.io/)
- AI powered by [OpenAI](https://openai.com/) and [Google Gemini](https://ai.google.dev/) (via [OpenRouter](https://openrouter.ai/))
- Web search via [Tavily](https://www.tavily.com/)
- Stock data via [Alpha Vantage](https://www.alphavantage.co/)
- Specialized Component Framework inspired by specialized agent frameworks
- Dynamic Plan Adjustment inspired by adaptive planning systems