"""
Tool registry for the ReAct application.
This module imports and registers all available tools.
"""
from .web_tools import web_search, web_scrape
from .file_tools import read_file, write_file, list_files, delete_file
from .enhanced_file_tools import enhanced_list_files
from .memory_tools import memory_get, memory_set, memory_list
from .knowledge_tools import kb_add_web, kb_add_file, kb_list, kb_get, kb_delete, kb_search
from .execution_tools import execute_python, reset_python_environment, list_python_variables
from .stock_tools import get_stock_data
from .firecrawl_tools import firecrawl_scrape, firecrawl_crawl, firecrawl_map
from .text_tools import text_extract_urls
from .system_tools import open_file

# Dictionary of all available tools
TOOLS = {
    "web_search": web_search,
    "web_scrape": web_scrape,
    "get_stock_data": get_stock_data,
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "delete_file": delete_file,
    "execute_python": execute_python,
    "reset_python_environment": reset_python_environment,
    "list_python_variables": list_python_variables,
    "memory_get": memory_get,
    "memory_set": memory_set,
    "memory_list": memory_list,
    "kb_add_web": kb_add_web,
    "kb_add_file": kb_add_file,
    "kb_list": kb_list,
    "kb_get": kb_get,
    "kb_delete": kb_delete,
    "kb_search": kb_search,
    "firecrawl_scrape": firecrawl_scrape,
    "firecrawl_crawl": firecrawl_crawl,
    "firecrawl_map": firecrawl_map,
    "text_extract_urls": text_extract_urls,
    "enhanced_list_files": enhanced_list_files,
    "open_file": open_file,
}
