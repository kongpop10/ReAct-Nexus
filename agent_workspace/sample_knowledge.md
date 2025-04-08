# Sample Knowledge Document

This is a sample markdown document that can be imported into the knowledge base.

## Key Information

- The ReAct app now supports a knowledge base feature
- Knowledge can be imported from web sources or local markdown files
- Knowledge base entries are automatically added to memory
- Knowledge base entries persist across conversations

## Usage Examples

1. Add a web page to the knowledge base:
   - Use the `kb_add_web` tool with a URL
   - The content will be scraped and stored

2. Add a local markdown file:
   - Use the `kb_add_file` tool with a filename
   - The file will be copied to the knowledge base

3. List all knowledge base entries:
   - Use the `kb_list` tool to see all entries

4. Get content from the knowledge base:
   - Use the `kb_get` tool with an entry ID or memory key

5. Search the knowledge base:
   - Use the `kb_search` tool with a query
