import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_workspace.format_results import escape_dollar_amounts, process_final_output

def test_dollar_amount_escaping():
    """Test the dollar amount escaping function with various inputs."""
    test_cases = [
        # Test case: Input text, Expected output
        ("The company reported revenue of $1029 million.", "The company reported revenue of \\$1029 million."),
        ("The price is $50.75 per share.", "The price is \\$50.75 per share."),
        ("$1,234,567.89 was the total cost.", "\\$1,234,567.89 was the total cost."),
        ("The equation $E=mc^2$ describes mass-energy equivalence.", "The equation $E=mc^2$ describes mass-energy equivalence."),
        ("Mixed content: $100 cash and the formula $F=ma$ for force.", "Mixed content: \\$100 cash and the formula $F=ma$ for force."),
        ("Multiple dollar amounts: $10, $20, and $30.", "Multiple dollar amounts: \\$10, \\$20, and \\$30."),
        ("No dollar amounts here!", "No dollar amounts here!"),
        ("$ by itself is not escaped.", "$ by itself is not escaped."),
        ("$1029 at the beginning of a line.", "\\$1029 at the beginning of a line."),
        ("At the end of a line: $1029", "At the end of a line: \\$1029"),
    ]
    
    for i, (input_text, expected_output) in enumerate(test_cases, 1):
        result = escape_dollar_amounts(input_text)
        if result == expected_output:
            print(f"✅ Test case {i} passed")
        else:
            print(f"❌ Test case {i} failed")
            print(f"   Input:    {input_text}")
            print(f"   Expected: {expected_output}")
            print(f"   Got:      {result}")

if __name__ == "__main__":
    print("Testing LaTeX processing functions...")
    test_dollar_amount_escaping()
    print("\nDone!")
