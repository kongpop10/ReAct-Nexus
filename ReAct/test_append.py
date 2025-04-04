from app import write_file

# Test appending to the file
result = write_file('test.txt', content='\nThis is appended text.', append=True)
print(result)
