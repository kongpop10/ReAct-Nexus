import sys
import os

# Add the parent directory to the path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import write_file

# Test appending to the file
result = write_file('test.txt', content='\nThis is appended text.', append=True)
print(result)
