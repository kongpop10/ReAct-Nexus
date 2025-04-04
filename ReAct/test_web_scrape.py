import sys
import json
from app import web_scrape

# Test with a list of URLs
urls = ['https://www.sciencedaily.com/news/computers_math/artificial_intelligence/',
        'https://techcrunch.com/category/artificial-intelligence/',
        'https://www.reuters.com/technology/artificial-intelligence/']

# Convert to string representation (as it might come from the AI)
urls_str = json.dumps(urls)

# Test the function with the string representation of the list using 'url' parameter
result = web_scrape(url=urls_str)
print("Result type (using 'url' parameter):", type(result))
print("Result (using 'url' parameter):", result[:500] + "..." if len(result) > 500 else result)

# Test with a single URL using 'url' parameter
single_url = 'https://www.sciencedaily.com/news/computers_math/artificial_intelligence/'
result_single = web_scrape(url=single_url)
print("\nSingle URL Result type (using 'url' parameter):", type(result_single))
print("Single URL Result (using 'url' parameter):", result_single[:500] + "..." if len(result_single) > 500 else result_single)

# Test with a list of URLs using 'urls' parameter
result_urls_param = web_scrape(urls=urls_str)
print("\nResult type (using 'urls' parameter):", type(result_urls_param))
print("Result (using 'urls' parameter):", result_urls_param[:500] + "..." if len(result_urls_param) > 500 else result_urls_param)

# Test with a single URL using 'urls' parameter
result_single_urls_param = web_scrape(urls=single_url)
print("\nSingle URL Result type (using 'urls' parameter):", type(result_single_urls_param))
print("Single URL Result (using 'urls' parameter):", result_single_urls_param[:500] + "..." if len(result_single_urls_param) > 500 else result_single_urls_param)
