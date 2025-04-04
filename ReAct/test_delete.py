import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import write_file, delete_file, list_files

# First, create a test file
print("Creating test file...")
write_result = write_file('test_to_delete.txt', content='This file will be deleted.')
print(write_result)

# List files to confirm it was created
print("\nListing files...")
list_result = list_files()
print(list_result)

# Now delete the file
print("\nDeleting the file...")
delete_result = delete_file('test_to_delete.txt')
print(delete_result)

# List files again to confirm it was deleted
print("\nListing files after deletion...")
list_result = list_files()
print(list_result)
