# ReAct: Conversational AI Workspace

A **modular Streamlit-based platform** integrating multiple AI models, real-time search, web scraping, stock data retrieval, conversation management, and Python code execution capabilities.

---

## Features

- **Conversational AI**: Chat with LLMs (OpenAI, Gemini via OpenRouter)
- **Automated Title Generation** for conversations using LLMs
- **Web Search**: Real-time queries via Tavily API
- **Web Scraping**: Extract content from URLs with BeautifulSoup
- **Stock Data Retrieval**: Fetch real-time stock info via Alpha Vantage API
- **Python Code Execution**: Run code snippets dynamically (demo purposes only; unsafe for production)
- **Conversation Management**:
  - Save/load conversations with metadata (title, timestamp)
  - Automatic conversation saving and indexing
  - Schema migration for legacy files
- **File Operations**: Read, write, delete, list files within a workspace directory
- **Memory Management**: Store and manage conversation context and variables

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

---

## Configuration

Create a `.env` file in the root directory and add your API keys:

```
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

These are required for AI completions, web search, and stock data respectively.

---

## Usage

Run the app with Streamlit:

```bash
streamlit run app.py
```

Navigate to the local URL provided by Streamlit to access the interface.

---

## Project Structure

```
/ReAct
│
├── ai_module/            # AI logic, planning, execution
│   ├── __init__.py
│   ├── ai_client.py
│
├── data_acquisition/     # Web scraping, news, APIs
│   ├── __init__.py
│   ├── news_scraper.py
│   ├── process_news.py
│   ├── process_search_results.py
│   ├── web_tools.py
│   ├── stock_data.py
│
├── processing/           # Text & LaTeX processing, formatting
│   ├── __init__.py
│   ├── latex_processor.py
│   ├── format_results.py
│   ├── text_processor.py
│
├── storage/              # File/memory management, conversations
│   ├── __init__.py
│   ├── file_utils.py
│   ├── memory_manager.py
│   ├── conversation_manager.py
│
├── tests/                # All tests
│   ├── __init__.py
│   ├── test_latex_processing.py
│
├── data/                 # Data files, conversation logs, scraped content
│   ├── conversations_index.json
│   ├── conversation_*.json
│   ├── *.txt
│
├── app.py                # Streamlit app entrypoint
├── requirements.txt
├── README.md
├── .gitignore
```

### Summary of key folders:

- **`ai_module/`**: AI interaction, planning, execution logic
- **`data_acquisition/`**: External data collection (scraping, APIs)
- **`processing/`**: Data post-processing, LaTeX handling, formatting
- **`storage/`**: Persistent storage, memory, conversation management
- **`tests/`**: Test scripts
- **`data/`**: Data files, logs, scraped content

---

## Additional Notes

- The reorganization improves modularity, clarity, and scalability.
- Data files (`*.json`, `*.txt`) are now centralized in the `data/` folder.
- Configurations via `.env` (API keys) are required.
- The app **allows arbitrary Python code execution**, which is **unsafe for production**—use only in a secure, sandboxed environment.
- Consider adding more tests and refactoring as needed.
- For configs/secrets, `.env` is recommended, but a dedicated `config/` folder can be added.

---

## License

MIT License

---

## Credits

- Built with [Streamlit](https://streamlit.io/)
- AI powered by [OpenAI](https://openai.com/) and Google Gemini (via OpenRouter)
- Web search via [Tavily](https://www.tavily.com/)
- Stock data via [Alpha Vantage](https://www.alphavantage.co/)