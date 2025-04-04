import os
import sys

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app import delete_file

# Test the delete_file function
result = delete_file('test_to_delete.txt')
print(result)

# Verify the file is deleted
print(f"File exists after deletion: {os.path.exists('agent_workspace/test_to_delete.txt')}")
