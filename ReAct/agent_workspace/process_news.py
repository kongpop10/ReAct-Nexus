import json
import os
from news_scraper import WebScraper

def main():
    # Sample articles from the failed execution
    articles = [
        {
            "title": "Artificial Intelligence News -- ScienceDaily",
            "url": "https://www.sciencedaily.com/news/computers_math/artificial_intelligence/",
            "snippet": "Mar. 18, 2025 — Virginia Tech researchers say a true revolution in wireless technologies..."
        },
        {
            "title": "Artificial intelligence | MIT News",
            "url": "https://news.mit.edu/topic/artificial-intelligence2",
            "snippet": "Show: News Articles In the Media Audio Creating a common language..."
        },
        {
            "title": "AI News & Artificial Intelligence | TechCrunch",
            "url": "https://techcrunch.com/category/artificial-intelligence/",
            "snippet": "AI News & Artificial Intelligence | TechCrunch AI News & Artificial Intelligence..."
        }
    ]

    try:
        # Ensure the output directory exists
        output_dir = os.path.dirname(os.path.abspath(__file__))

        # Create a WebScraper instance
        scraper = WebScraper()

        # Process articles and get content
        processed_articles = scraper.process_items(articles)

        # Save articles to files
        scraper.save_items(processed_articles, output_dir)
        print("Successfully processed and saved all articles.")

    except Exception as e:
        print(f"Error in main process: {str(e)}")

if __name__ == '__main__':
    main()