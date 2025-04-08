import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
import json
import time
import random
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class WebScraper:
    def __init__(self,
                 delay_range: tuple = (1, 3),
                 max_content_length: int = 4000,
                 unwanted_elements: Set[str] = {'script', 'style', 'nav', 'header', 'footer'},
                 retry_attempts: int = 3,
                 timeout: int = 10):
        self.delay_range = delay_range
        self.max_content_length = max_content_length
        self.unwanted_elements = unwanted_elements
        self.retry_attempts = retry_attempts
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }
        self._setup_session()

    def _setup_session(self) -> None:
        """Set up a requests session with retry configuration."""
        self.session = requests.Session()
        retries = Retry(
            total=self.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def scrape_content(self, url: str) -> str:
        """Scrapes the text content of a given URL with retries and proper error handling."""
        try:
            time.sleep(random.uniform(*self.delay_range))  # Polite delay between requests
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted elements
            for element in soup(list(self.unwanted_elements)):
                element.decompose()

            # Get text content
            paragraphs = soup.find_all('p')
            text = ' '.join(p.get_text().strip() for p in paragraphs)

            # If no paragraphs found, get all text
            if not text:
                text = soup.get_text(separator=' ', strip=True)

            # Process text to handle LaTeX and dollar amounts
            processed_text = self._process_latex_and_dollars(text)

            return processed_text[:self.max_content_length]
        except requests.exceptions.RequestException as e:
            return f"Error scraping {url}: {str(e)}"
        except Exception as e:
            return f"Unexpected error while scraping {url}: {str(e)}"

    def _process_latex_and_dollars(self, text: str) -> str:
        """
        Process text to handle LaTeX expressions and dollar amounts.

        This function prevents confusion between LaTeX delimiters ($) and dollar amounts ($123).

        Args:
            text (str): The input text to process

        Returns:
            str: Processed text with dollar amounts properly escaped
        """
        # Pattern to match dollar amounts: $ followed by digits
        # This regex looks for $ followed by digits, with optional commas and decimal point
        dollar_pattern = r'(\$)(\d{1,3}(,\d{3})*(\.[0-9]+)?|\d+(\.[0-9]+)?)'

        # Replace with escaped dollar sign for Markdown
        escaped_text = re.sub(dollar_pattern, r'\\\1\2', text)

        return escaped_text

    def process_items(self, items: List[Dict], required_fields: Set[str] = {'url', 'title'}) -> List[Dict]:
        """Process a list of item dictionaries and add scraped content."""
        processed_items = []

        for item in items:
            if not all(field in item for field in required_fields):
                continue

            content = self.scrape_content(item['url'])
            processed_item = item.copy()
            processed_item['content'] = content
            processed_items.append(processed_item)

        return processed_items

    def save_items(self, items: List[Dict], base_path: str, prefix: str = 'scraped_item') -> None:
        """Save processed items to individual files with customizable prefix."""
        for i, item in enumerate(items, 1):
            filename = f"{base_path}/{prefix}_{i}.txt"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for key, value in item.items():
                        if key != 'content':
                            f.write(f"{key.title()}: {value}\n\n")
                    f.write(f"Content:\n{item.get('content', '')}")
            except IOError as e:
                print(f"Error saving item {i}: {str(e)}")