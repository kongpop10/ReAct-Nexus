import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import write_file, read_file

# First, read the current content
print("Current content of test.txt:")
current_content = read_file('test.txt')
print(current_content)

# Now append to the file with explicit append=True
print("\nAppending to the file...")
result = write_file('test.txt', content='\nThis is explicitly appended text.', append=True)
print(result)

# Read the file again to verify
print("\nNew content after appending:")
new_content = read_file('test.txt')
print(new_content)
