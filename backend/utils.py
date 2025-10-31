# backend/utils.py

def add_numbers(a, b):
    """
    Adds two numbers together.
    """
    if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        raise TypeError("Inputs must be numbers")
        
    return a + b

def get_greeting(name):
    """
    Returns a greeting message.
    """
    if not name:
        return "Hello, stranger!"
    return f"Hello, {name}!"

def subtract_numbers(a, b):
    """
    Subtracts b from a.
    """
    return a - b