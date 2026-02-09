import random
import re

def spin(text):
    """
    Parses Spintax format {a|b|c} and returns a random variation.
    Supports nested spintax like {Hi|Hello {there|friend}}.
    """
    if not text:
        return ""
    
    # Regex to find the innermost {option1|option2} pattern
    pattern = r'\{([^{}]+)\}'
    
    while True:
        match = re.search(pattern, text)
        if not match:
            break
            
        # Extract the content inside braces
        content = match.group(1)
        # Split by pipe |
        options = content.split('|')
        # Choose random option
        choice = random.choice(options)
        
        # Replace the first occurrence with the choice
        text = text[:match.start()] + choice + text[match.end():]
        
    return text

if __name__ == "__main__":
    # Test cases
    test_str = "{Hi|Hello|Hey} [Name], {I was looking at|I came across} your {listing|profile}."
    print(f"Original: {test_str}")
    print(f"Spun 1: {spin(test_str)}")
    print(f"Spun 2: {spin(test_str)}")
    print(f"Spun 3: {spin(test_str)}")
