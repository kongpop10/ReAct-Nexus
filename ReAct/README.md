# AI Agent Workspace

This is a **Streamlit-based conversational AI workspace** integrating multiple AI models, web search, scraping, stock data retrieval, conversation management, and Python code execution.

## Features

- **Conversational AI**: Chat with LLMs (OpenAI, Gemini via OpenRouter)
- **Automated Title Generation** for conversations using LLMs
- **Web Search**: Real-time search via Tavily API
- **Web Scraping**: Extracts content from URLs with BeautifulSoup
- **Stock Data Retrieval**: Fetches real-time stock info via Alpha Vantage API
- **Python Code Execution**: Run code snippets dynamically (demo, unsafe for production)
- **Conversation Management**:
  - Save/load conversations with metadata (title, timestamp)
  - Automatic conversation saving and indexing
  - Schema migration for legacy files
- **File Operations**: Read, write, delete, list files within a workspace directory
- **Memory Management**: Store and manage conversation context and variables

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

## Configuration

Create a `.env` file in the root directory and add your API keys:

```
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

These are required for AI completions, web search, and stock data respectively.

## Usage

Run the app with Streamlit:

```bash
streamlit run app.py
```

Navigate to the local URL provided by Streamlit to access the web interface.

## Project Structure

```
app.py                     # Main Streamlit app with integrated tools
ai_client.py               # AI client logic
conversation_manager.py    # Conversation history management
memory_manager.py          # Memory/context management
file_utils.py              # File utility functions
stock_data.py              # Stock API integration
web_tools.py               # Web scraping and search tools

agent_workspace/           # Workspace directory for saved files & conversation data
  ├── news_scraper.py
  ├── latex_processor.py
  ├── process_news.py
  ├── process_search_results.py
  └── (saved conversation JSON files)
```

## Security Warning

- **The app allows arbitrary Python code execution via `exec()`. This is unsafe for production use.**
- Use in a secure, sandboxed environment only.

## License

[Specify your license here]

## Credits

- Built with [Streamlit](https://streamlit.io/)
- AI powered by [OpenAI](https://openai.com/) and Google Gemini (via OpenRouter)
- Web search via [Tavily](https://www.tavily.com/)
- Stock data via [Alpha Vantage](https://www.alphavantage.co/)