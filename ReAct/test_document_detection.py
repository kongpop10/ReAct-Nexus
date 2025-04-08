"""
Test script for document URL detection and redirection to Firecrawl.
"""
import os
import streamlit as st
import sys

# Mock Streamlit session state for testing
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# Import after setting up mock session state
from tools.web_tools import is_document_url

def test_document_detection():
    """Test the document URL detection function."""
    test_urls = [
        # PDF URLs
        "https://example.com/document.pdf",
        "https://example.com/files/report.pdf",
        "https://example.com/download?format=pdf",
        "https://example.com/pdf/whitepaper",
        
        # Office document URLs
        "https://example.com/presentation.pptx",
        "https://example.com/spreadsheet.xlsx",
        "https://example.com/document.docx",
        "https://example.com/download?format=docx",
        "https://example.com/files/report.doc",
        
        # Other document formats
        "https://example.com/ebook.epub",
        "https://example.com/archive.zip",
        "https://example.com/data.csv",
        
        # Non-document URLs
        "https://example.com",
        "https://example.com/about",
        "https://example.com/blog/article",
        "https://example.com/contact.html",
        "https://example.com/products.php",
    ]
    
    print("Testing document URL detection...\n")
    
    for url in test_urls:
        is_document = is_document_url(url)
        result = "DOCUMENT" if is_document else "REGULAR WEBPAGE"
        print(f"{url:<50} -> {result}")

if __name__ == "__main__":
    test_document_detection()
