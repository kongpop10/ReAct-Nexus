"""
Test script for the enhanced file listing integration.
This script simulates the processing of a file listing response.
"""
import os
import streamlit as st
import sys

# Mock Streamlit session state for testing
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# Import after setting up mock session state
from processing.file_listing_handler import process_file_listing_response
from tools.file_tools import list_files

def main():
    """Test the enhanced file listing integration."""
    print("Testing enhanced file listing integration...\n")
    
    # Test the list_files function
    print("Using list_files function:\n")
    result = list_files()
    print(result)
    
    # Test the process_file_listing_response function with a simple file listing
    print("\nTesting process_file_listing_response with a simple file listing:\n")
    simple_listing = """file1.txt
file2.md
file3.py
directory1
directory2
config.json"""
    
    processed = process_file_listing_response(simple_listing)
    print(processed)
    
    # Test with a non-file listing response
    print("\nTesting with a non-file listing response:\n")
    non_file_listing = "This is a regular response that is not a file listing."
    processed = process_file_listing_response(non_file_listing)
    print(processed)

if __name__ == "__main__":
    main()
