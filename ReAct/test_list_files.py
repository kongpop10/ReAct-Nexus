import os
import sys

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app import list_files

# Test the list_files function without a directory parameter
print("Listing files in the workspace directory:")
result = list_files()
print(result)

# Test the list_files function with a directory parameter
print("\nListing files in a subdirectory (if it exists):")
result = list_files(directory="agent_workspace")
print(result)

# Test with a non-existent directory
print("\nListing files in a non-existent directory:")
result = list_files(directory="non_existent_directory")
print(result)
