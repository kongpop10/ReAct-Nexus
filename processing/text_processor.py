from .latex_processor import process_latex_in_text

def process_text_output(text):
    """
    Process any text output before it's displayed to the user.
    This function applies various text processing steps including LaTeX handling.
    
    Args:
        text (str): The input text to process
        
    Returns:
        str: Processed text ready for display
    """
    # Process LaTeX expressions
    processed_text = process_latex_in_text(text)
    
    # Additional text processing could be added here
    
    return processed_text
